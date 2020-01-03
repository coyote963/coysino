# import the enum type for rcon events
from rcontypes import rcon_event, rcon_receive
# import json parsing to translate server messages into JSON type
import random
import json
from db import CasinoPlayer, Player, PlayerAccount
#optional: add in automatic table lookup for translating PlayerID's to Player Profile + Store
from update_cache import get_handle_cache
from mongoengine import DoesNotExist
from helpers import send_packet
# player dict for this scope only, useful for packets that only have playerId
player_dict = {}
handle_cache = get_handle_cache(player_dict)


def get_visiblity(casino_player : CasinoPlayer, message  : str, player_id : str, sock):
    if message.startswith("!visible"):
        if casino_player.visibility:
            pm = "public profile"
        else:
            pm = "private profile"
        pm += " !toggle to switch"
        cmd = 'pm "{}" "{}" "{}"'.format(player_id, pm, "9090242")
        send_packet(sock, cmd, rcon_receive.command.value)

def toggle(casino_player : CasinoPlayer, message  : str, player_id : str, sock):
    if message.startswith("!toggle"):
        if casino_player.visibility:
            pm = "Profile has been set to private"
        else:
            pm = "Profile has been set to public"
        casino_player.visibility = not casino_player.visibility
        casino_player.save()

        cmd = 'pm "{}" "{}" "{}"'.format(player_id, pm, "9090242")
        send_packet(sock, cmd, rcon_receive.command.value)

def upsert_player(profile_id : dict):
    """Updates and returns a new Casino Player, if the underlying player object does not exist, returns with an error"""
    player_prof = PlayerAccount(
        platform = profile_id['StoreID'],
        profile = profile_id['ProfileID']
    )
    try:
        db_player = Player.objects.get(profile = player_prof)
    except DoesNotExist:
        raise Exception("The player object associated with this account does not exist:\n{}".format(profile_id))
    try:
        casino_player = CasinoPlayer.objects.get(player = db_player)
    except DoesNotExist:
        casino_player = CasinoPlayer(player = db_player)
    casino_player.save()
    return [casino_player, db_player]

def pay(casino_player : CasinoPlayer, message  : str, player_id : str, sock):
    if message.startswith("!pay"):
        msg = "Added your daily pay"
        casino_player.balance += casino_player.daily
        casino_player.daily = 0
        casino_player.save()
        cmd = 'rawsay "{}" "{}"'.format(msg, "8421376")
        send_packet(sock, cmd, rcon_receive.command.value)

def check_balance(casino_player : CasinoPlayer, message  : str, player_id : str, sock):
    if message.startswith("!balance"):
        pm = "Your balance is {}c. Use !pay to withdraw {}c".format(casino_player.balance, casino_player.daily)
        if casino_player.visibility:
            cmd = 'rawsay "{}" "{}"'.format(pm, "8421376")
        else:
            cmd = 'pm "{}" "{}" "{}"'.format(player_id, pm , "9090242")
        send_packet(sock, cmd, rcon_receive.command.value)




def roll(casino_player : CasinoPlayer, message  : str, player_id : str, sock):
    if message.startswith("!flip"):
        arguments = message.split(" ")
        if len(arguments) == 3:
            print(arguments)
            if arguments[2].isdigit():
                if casino_player.balance > int(arguments[2]):
                    if arguments[1] == "h" or arguments[1] == "t":
                        coin = random.randint(0, 1)
                        if coin == 1:
                            pm = "flips a coin... it is {}. Looks like you won :gold: ".format(arguments[1])
                            casino_player.balance += int(arguments[2])
                        else:
                            pm = "flips a coin... Looks like you lost :spasdead: ".format(arguments[1])
                            casino_player.balance -= int(arguments[2])
                        casino_player.save()
                    else:
                        pm = "first argument must be either h or t"
                else:
                    pm = "insufficient funds"
            else:
                pm = "provide a number"
        else:
            pm = "flip a coin: !flip <prediction h/t> <number amount>"
        if casino_player.visibility:
            cmd = 'rawsay "{}" "{}"'.format(pm, "8421376")
        else:
            cmd = 'pm "{}" "{}" "{}"'.format(player_id, pm , "9090242")
        send_packet(sock, cmd, rcon_receive.command.value)

def get_help(casino_player : CasinoPlayer, message : str, player_id : str, sock):
    if message.startswith("!help"):
        arguments = message.split(" ")
        if len(arguments) == 2 and arguments[1] in ['flip', 'pay', 'balance', 'visible', 'toggle']:
            if arguments[1] == 'flip':
                pm = "Make a <guess> and flip a coin. You either lose or gain depending on your <amount>. [!flip <guess> <amount>]"
            if arguments[1] == 'pay':
                pm = "Transfer your earnings into your balance. Your earnings come from getting kills. [!pay]"
            if arguments[1] == 'balance':
                pm = "Check your balance [!balance]"
            if arguments[1] == 'visible':
                pm = "Check your visibility settings. Depending on your setting, Coysino will either pm you or display publicly"
            if arguments[1] == 'toggle':
                pm = "Toggles your visibility setting"
        else:
            pm = "Welcome to the Coysino. The commands are flip, pay, balance, visible, toggle. Do !help <command> for information on that command"
        cmd = 'rawsay "{}" "{}"'.format(pm, "8421376")
        send_packet(sock, cmd, rcon_receive.command.value)

def handle_kill(event_id, message_string, sock):
    if event_id == rcon_event.player_death.value:
        js = json.loads(message_string)
        try:
            casino_player = upsert_player(json.loads(js['KillerProfile']))[0]
        except:
            return
        casino_player.daily += 10
        casino_player.save()


def handle_chat(event_id, message_string, sock):
    # if passed in event_id is a chat_message
    if event_id == rcon_event.chat_message.value:
        # parse the json
        js = json.loads(message_string)
        # if the server message is from a player
        if 'PlayerID' in js and js['PlayerID'] != '-1':
            try:
                casino_player, db_player = upsert_player(json.loads(js['Profile']))
            except Exception as e:
                print(str(e))
                return
            funclist = [pay, roll, check_balance, get_visiblity, toggle, get_help]
            for f in funclist:
                f(casino_player, js['Message'], js['PlayerID'], sock)





casino_functions  = [handle_cache, handle_chat, handle_kill] # include handle_cache if you are using it