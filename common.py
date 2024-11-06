from dataclasses import dataclass
from typing import Any, Self
import discord
import os

IS_USER = False #if I'm running the bot, IS_USER = False

@dataclass
class UserInfo:
  user_id:str
  username:str
  displayname:str

  @staticmethod
  def from_ctx(ctx: discord.ApplicationContext):
    return UserInfo.from_user(ctx.author)
  
  @staticmethod
  def from_int(interaction: discord.Interaction):
    return UserInfo.from_user(interaction.user)
  
  @staticmethod
  def from_user(user)->Self:
    return UserInfo(user.id, user.name, user.global_name)
  
EMOJIS = {
  'rainy': "<:rainy:1147532768604078153>",
  'glad': "<:glad:1079797689375539221>",
  'yellow': "<:yellow:1249859238650576927>"
}

def emoji(s:str)->str:
  if not IS_USER:
    return EMOJIS[s]
  return ""

def get_env_ints(name):
  return list(map(int, os.getenv(name).split(',')))

def flatten(s):
  def flatten_inner(acc:[Any], ss:Any):
    if hasattr(ss, '__iter__'):
      for i in ss:
        acc.extend(flatten(i))
      return acc
    else:
      acc.append(ss)
    return acc
      
  return flatten_inner([], s)

def test_flatten():
  testcases = [
    ([1], [1]),
    ([[1]], [1]),
    ([[1, 2, 3], 1], [1, 2, 3, 1]),
    ([[[1,2,3], [1]], [1,2,3]], [1,2,3,1,1,2,3])
  ]
  for l, expected in testcases:
    flattened = flatten(l)
    if expected != flattened:
      print(f"Test FAIL on {l} expected {expected} got {flattened}")

