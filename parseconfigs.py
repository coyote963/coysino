
# IP Address of the host
ip = 'localhost'
# Gamemode to port mapping
gamemode_ports = { 'b' : 7778,'c' : 7779, 'd' : 7780, 'e' : 7781}

#server rcon password
password = 'ur password here'

# set to true for performance, set to false for reliability
blocking = True


#helper function to get the port given a gamemode
def get_port(gamemode):
    return gamemode_ports[gamemode]