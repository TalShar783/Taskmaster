import enum
import os
import pygsheets
import dice
from datetime import datetime
import discord_token
import discord
from discord import app_commands
from aenum import extend_enum

"""
########################################################################################################################
Internal Bot Stuff and GSheet Interactions
########################################################################################################################
"""

# Your keyfile should be a JSON generated on the Google Developer Console, located in the same folder as this script.
# Currently it's set to expect Linux nomenclature and attempt Windows if that fails, but I can't make any promises.
try:
    keyfile_path = f"{os.getcwd()}/keyfile.json"
except FileNotFoundError:
    keyfile_path = f"{os.getcwd()}\\keyfile.json"
gc = pygsheets.authorize(service_file=keyfile_path)
sh = gc.open(discord_token.MY_WORKSHEET)
transactions = sh.worksheet_by_title('Transactions')
tasks = sh.worksheet_by_title('Task List')
totals = sh.worksheet_by_title('Totals')

task_list: dict = {}
user_list: list = []
debug_enabled = True


def debug(message: str):
    if debug_enabled:
        print(message)


UserEnum = enum.Enum('UserEnum', {'Everyone': 'Everyone'})
TaskEnum = enum.Enum('TaskEnum', {})


def register_tasks():
    global task_list
    task_list = {}
    all_tasks = tasks.get_values(include_tailing_empty_rows=False, include_tailing_empty=False, start="A:A", end="E:E")
    for this_task in all_tasks:
        task_name = this_task[0] if this_task[0:] else "ERROR"
        task_reward = this_task[1] if this_task[1:] else "Blank"
        task_average = this_task[2] if this_task[2:] else "Blank"
        task_notes = this_task[3] if this_task[3:] else ""
        task_list[this_task[0]] = {
            "Task": task_name,
            "Reward": task_reward,
            "Average": task_average,
            "Notes": task_notes
        }
    del task_list["Task"]
    for task in task_list:
        try:
            extend_enum(TaskEnum, task, task)
        except Exception as e:
            debug(f"Got exception when assigning task to TaskEnum: {e}")


def register_users():
    global user_list
    try:
        user_list = totals.get_values(include_tailing_empty=False, include_tailing_empty_rows=False, start="1:1",
                                      end="1:1")[0]
        for user in user_list:
            try:
                extend_enum(UserEnum, user, user)
            except Exception as e:
                debug(f"Got exception when adding user to UserEnum: {e}")

        user_list.append("Everyone")
        return user_list
    except Exception as e:
        debug(f"Got exception in registering users: {e}")


def get_task(task: str):
    """
    :param task: = A string exactly matching the name of the task in the spreadsheet
    :returns task as dict: Returns a dictionary object containing the task named.
    """

    try:
        debug(f"task is: {task}")
        return task_list[task]
    except Exception as e:
        debug(f"Got exception in getting task: {e}")


def get_task_name(task: str):
    return get_task(task)["Task"]


def get_reward(task: str):
    debug(f"task={task}")
    return get_task(task)["Reward"]


def get_average(task: str):
    return get_task(task)["Average"]


def get_notes(task: str):
    return get_task(task)["Notes"]


def calculate_reward(amount: str):
    """
    Takes a String amount. Should look something like "2d6 +8".
    Can take static values ("20").
    Uses github.com/borntyping/python-dice
    """

    try:
        return dice.roll(f"{amount}t")
    except Exception as e:
        debug(f"Got exception when attempting to calculate reward: {e}")


def record_task(task: str, recorder: str, notes: str = ""):
    """
    Takes the name of a task you've completed as well as an optional notes.
    Then, calculates your reward, reports it, and adds an entry to the table.
    """
    debug(f"task={task}, \nrecorder={recorder},\nnotes={notes}")
    reward = get_reward(task)
    amount = calculate_reward(reward)
    notes = f"{notes} - Added by Bot"
    date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    transactions.append_table(values=[date, recorder, task, amount, notes], start='A:A', end='E:E')
    debug(f"reward={reward}\n recorder={recorder}\n amount={amount} \n notes={notes} \n date={date}")
    return f"Task completion recorded for {recorder}! You earned ${amount}! Current balance: {check_balance(recorder)}."


def spend(amount: float = 0.0, reason: str = "", spender: str = "", notes: str = ""):
    try:
        notes = f"{notes} - Added by Bot"
        date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        transactions.append_table(values=[date, spender, reason, -abs(amount), notes], start="A:A", end="E:E")
        return f"Transaction recorded for {spender} at {date} for {reason}: ${amount}. Notes: {notes}"
    except Exception as e:
        debug(f"Got exception when attempting to add a spend transaction: {e}")


def earn(amount: float = 0.0, reason: str = "", earner: str = "", notes: str = ""):
    try:
        notes = f"{notes} - Added by Bot"
        date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        transactions.append_table(values=[date, earner, reason, abs(amount), notes], start="A:A", end="E:E")
        return f"Transaction recorded for {earner} at {date} for {reason}: ${amount}. Notes: {notes}"
    except Exception as e:
        debug(f"Got exception when attempting to add an earn transaction: {e}")


def check_balance(name: str = ""):
    if name == "Everyone":
        return "N/A"
    try:
        debug(f"name = {name}")
        address: tuple = totals.find(forceFetch=True, matchEntireCell=True, pattern=name)[0].address.index
        cell: tuple = tuple([int(address[0] + 1), int(address[1])])
        debug(f"name address: {address} \nvalue address: {cell}")
        debug(f"value of value address: {totals.get_value(addr=cell)}")
        return totals.get_value(addr=cell)
    except Exception as e:
        debug(f"Got exception when attempting to check balance: {e}")


def reset_bot():
    global task_list
    global user_list
    task_list = {}
    user_list = []
    register_tasks()
    register_users()


# Tasks and Users must be registered now, otherwise when the bot tries to register its commands, it will fail
# because it won't have the proper values for its Enums.
register_tasks()
register_users()

"""
########################################################################################################################
Discord Integration Things
########################################################################################################################
"""

# TOKEN needs to be your Discord client's private token. mytoken.py is not included in the repository. To use it,
# just make a mytoken.py file and assign your token to the "token" variable.

TOKEN = discord_token.MY_TOKEN
MY_GUILD = discord.Object(id=discord_token.MY_GUILD)


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default(), )
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync()


client = MyClient()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.tree.command()
async def debug_switch(interaction: discord.Interaction):
    global debug_enabled
    if debug_enabled:
        debug_enabled = False
        print("Debug disabled.")
        await interaction.response.send_message("Debug disabled.")
    else:
        debug_enabled = True
        print("Debug enabled.")
        await interaction.response.send_message("Debug disabled.")


@client.tree.command()
async def reset(interaction: discord.Interaction):
    reset_bot()
    await interaction.response.send("Bot reset.")


@client.tree.command()
@app_commands.describe(name="The name of the person who did the task.",
                       task="The name of the task.",
                       notes="Any notes you might want to add."
                       )
async def record(interaction: discord.Interaction,
                 name: UserEnum,
                 task: TaskEnum,
                 notes: str = ""):
    reply = record_task(
        recorder=name.value,
        task=task.value,
        notes=notes)
    await interaction.response.send_message(reply)


@client.tree.command(name="earn")
@app_commands.describe(name="The name of the person who earned the money.",
                       reason="What you did to earn the money.",
                       amount="The amount of money earned  (enter a decimal with no $, eg. '4.20')")
async def earn_money(interaction: discord.Interaction,
                     name: UserEnum,
                     reason: str = "",
                     amount: float = 0.0,
                     notes: str = ""):
    await interaction.response.send_message(earn(
        earner=name.value,
        reason=reason,
        amount=amount,
        notes=notes))


@client.tree.command(name="spend")
@app_commands.describe(name="The name of the person who spent the money.",
                       reason="What did you spend the money on?",
                       amount="The amount of money spent (enter a decimal with no $, eg. '4.20').")
async def spend_money(interaction: discord.Interaction,
                      name: UserEnum,
                      reason: str = "",
                      amount: float = 0.0,
                      notes: str = ""):
    await interaction.response.send_message(spend(
        spender=name.value,
        reason=reason,
        amount=amount,
        notes=notes))


@client.tree.command(name="check_balance")
@app_commands.describe(name="The name of the person whose balance you want to check.")
async def d_check_balance(interaction: discord.Interaction,
                          name: UserEnum):
    first_interaction = interaction
    try:
        balance = f"Balance for {name.value}: {check_balance(name.value)}."
    except Exception as e:
        debug(f"Error in accessing sheet to get balance: {e}")
        balance = "Error"
    try:
        debug(balance)
        await first_interaction.response.send_message(balance)
    except Exception as e:
        debug(f"Got exception when attempting to send response for check_balance: {e}")
        await first_interaction.followup.send(balance)


"""
########################################################################################################################
Definitions are done, below here we're DOING THINGS!
########################################################################################################################
"""

# Turn on the bot and log it into Discord.
client.run(TOKEN)
