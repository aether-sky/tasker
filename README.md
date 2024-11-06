
# Tasker
Tasker is a discord bot that allows users to commit to focused time for a set number of minutes. Each session is tracked and the user can ask for a summary of their sessions.

## Running the bot:
1) Create a .env file with the following values:

 - `TOKEN=<token of your discord app>` 
 - `GUILD_IDS=<comma separated list of IDs, no spaces>` - The Guild IDs where the bot runs.
 - `ALLOWED_CHANNELS=<comma separated list of IDs, no spaces>` - The allowed channels where the `/session` and `/summary` commands may be run.
 - `POSTGRES_PASSWORD=<password>` - Password for the postgres instance. Can be anything.
 - `TEST_CHANNELS=<comma separated list of IDs, no spaces>` - Channels for testing where commands may be run, but are flagged as test values in the database.

To run the bot, simply run `docker compose up --build -d`. This will require having docker installed on your system.

## Commands:
**/session** - Begin a session for a specified duration of time. Optionally one can provide a summary of what work they intend to accomplish during the session and how many minutes in the future the session will begin.

Sessions are completed by clicking the "Complete session" button attached to the bot's response.

**/summary** - Provides a summary of how many sessions and how much total focused time the user has completed.