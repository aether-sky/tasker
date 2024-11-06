import discord
import os
import dotenv
import db
import psycopg
from common import *
from discord.commands import Option
from discord.ui import View, Modal, InputText
from discord.ext import tasks
import time
import logging

#logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()

MY_GUILD_IDS = get_env_ints("GUILD_IDS")
ALLOWED_CHANNELS = get_env_ints("ALLOWED_CHANNELS")
TEST_CHANNELS = get_env_ints("TEST_CHANNELS")

bot = discord.Bot()

@tasks.loop(minutes=15)
async def session_cleanup():
  print(f"Closing stale sessions")
  closed = db.close_stale_sessions()
  print(f"Closed {closed} sessions")

session_cleanup.start()

@bot.event
async def on_command_error(ctx, error):
    print(f"Error: {error}")

@bot.event
async def on_ready() -> None:
  print(f"{bot.user} is ready and online!")
  db.close_stale_sessions()
  session_user_ids = db.load_session_buttons()
  for id_ in session_user_ids:
    print(f"Re-attaching session id {id_}")
    bot.add_view(SessionView(id_))


def perm_check(ctx: discord.ApplicationContext):
  return ctx.channel.id in ALLOWED_CHANNELS

def perm_fail(ctx: discord.ApplicationContext):
  return ctx.respond("Command not allowed in this channel!", ephemeral=True)

class SessionModal(Modal):
  def __init__(self, message):
    super().__init__(title="How'd it go?")
    self.add_item(InputText(label="Session summary", 
                            placeholder="Type how the session went..."))
    self.message = message

  async def callback(self, interaction: discord.Interaction):
    user_input = self.children[0].value
    rstring = "Session completed!"
    if user_input:
      rstring += f"\n\n{interaction.user.global_name}'s summary: *{user_input}*"
    await interaction.response.send_message(rstring)
    await self.message.edit(view=View())
    db.end_session(UserInfo.from_int(interaction), user_input)

class SessionButton(discord.ui.Button):
  def __init__(self, origin_user_id:int):
    super().__init__(label="Complete session", 
                     style=discord.ButtonStyle.primary, 
                     custom_id="session" + str(origin_user_id))
    self.origin_user_id = origin_user_id

  async def callback(self, interaction):
    if interaction.user.id != self.origin_user_id:
      await interaction.response.send_message(f"You can't complete someone else's session {emoji('yellow')}", ephemeral=True)
    else:
      await interaction.response.send_modal(SessionModal(interaction.message))

class SessionCancelButton(discord.ui.Button):
  def __init__(self, origin_user_id:int):
    super().__init__(label="Cancel", 
                     style=discord.ButtonStyle.primary, 
                     custom_id="cancel" + str(origin_user_id))
    self.origin_user_id = origin_user_id

  async def callback(self, interaction):
    if interaction.user.id != self.origin_user_id:
      await interaction.response.send_message(f"You can't cancel someone else's session {emoji('yellow')}", ephemeral=True)
    else:
      content = f"~~{interaction.message.content}~~ Session canceled"
      await interaction.message.edit(view=View(), content=content)
      await interaction.response.send_message("Session canceled.", ephemeral=True)


class SessionView(discord.ui.View):
  def __init__(self, origin_user_id:int):
    super().__init__(timeout=None)
    self.origin_user_id = origin_user_id
    self.custom_id = str(origin_user_id)
    self.add_item(SessionButton(origin_user_id))
    self.add_item(SessionCancelButton(origin_user_id))


@bot.slash_command(
    name="session", 
    description="Start a session",
    guild_ids=MY_GUILD_IDS)
async def session(ctx: discord.ApplicationContext, 
                  duration: Option(int, "The duration of the session in minutes"), 
                  intention: Option(str, "What you're going to work on (string)", default=""), 
                  when:Option(int,"When you're going to start the session (in minutes from now)",default=0)) -> None:
  if not perm_check(ctx):
    await perm_fail(ctx)
  else:
    user = UserInfo.from_ctx(ctx)
    is_test = ctx.channel.id in TEST_CHANNELS
    db.start_session(user, duration, intention, when, is_test)

    rstring = f"**{user.displayname}** is starting a session for {duration} minutes"
    if when != 0:
      t = int(time.time()) + when*60
      rstring += " at <t:%d:t>" % t
    else:
      rstring += " right now"
    if intention:
      rstring += ": *" + intention + "*"

    view = SessionView(user.user_id)
    await ctx.respond(rstring, view=view)

@bot.slash_command(
    name="summary", 
    description="Print a summary of completed sessions",
    guild_ids=MY_GUILD_IDS)
async def summary(ctx: discord.ApplicationContext):
  user = UserInfo.from_ctx(ctx)
  summary = db.get_summary(user)
  await ctx.respond(summary)

def main() -> None:
  try:
    db.setup()
  except psycopg.DatabaseError as e:
    print(f"Error: {e}")
    return
  bot.run(os.getenv('TOKEN'))

if __name__ == '__main__':
  test_flatten()
  main()


