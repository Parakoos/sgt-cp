import adafruit_logging as logging
log = logging.getLogger()
import json
import time

def simplify_color(color):
    return (simplify_color_part(color[0]), simplify_color_part(color[1]), simplify_color_part(color[2]))

def simplify_color_part(color_part):
    return (color_part//86)*127

def get_state_float(state, key, default=0):
    return float(state[key]) if key in state and state[key] != None and state[key] != "" else default

def get_state_int(state, key, default=0):
    return int(state[key]) if key in state and state[key] != None and state[key] != "" else default

def get_state_string(state, key, default=""):
    return state[key] if key in state and state[key] != None else default

def get_action_string(actions, key):
    return actions[key]['action'] if key in actions and actions[key] != None else None

class GameState():
    # Constants
    STATE_PLAYING = 'pl'
    STATE_ADMIN = 'ad'
    STATE_PAUSE = 'pa'
    STATE_START = 'st'
    STATE_FINISHED = 'en'
    STATE_NOT_CONNECTED = 'nc'
    STATE_RUNNING = 'ru'
    STATE_NOT_RUNNING = 'nr'
    STATE_SIM_TURN = 'si'

    TIMER_MODE_COUNT_UP = 'cu'
    TIMER_MODE_COUNT_DOWN = 'cd'
    TIMER_MODE_SAND_TIMER = 'st'
    TIMER_MODE_NO_TIMER = 'nt'

    def __init__(self,
                 ble_state_string: str = None, ble_field_order: list[str] = None, ble_field_divider: str = None,
                 json_state_string: str = None,
                 timestamp_offset = 0):
        state = {}
        if (json_state_string != None):
            state = json.loads(json_state_string)
        elif ble_state_string != None and ble_field_order != None and ble_field_divider != None:
            values = ble_state_string.split(ble_field_divider)
            if len(values) != len(ble_field_order):
                raise Exception(f"Different number of values from the keys. ({len(values)} != {len(ble_field_order)})")
            state["ts"]=time.monotonic()

            simple_mappings = [
                ('sgtTimerMode', 'timerMode'),
                ('sgtColor', 'color'),
                ('sgtTurnTime', 'turnTime'),
                ('sgtState', 'state'),
                ('sgtName', 'name'),
                ('sgtSeat', 'seat'),
                ('sgtPlayerTime', 'playerTime'),
                ('sgtTotalPlayTime', 'totalPlayTime'),
                ('sgtActionAdmin', 'actionAdmin'),
                ('sgtActionInactive', 'actionInactive'),
                ('sgtActionPause', 'actionPause'),
                ('sgtActionPrimary', 'actionPrimary'),
                ('sgtActionSecondary', 'actionSecondary'),
                ('sgtActionUndo', 'actionUndo'),
                ('sgtGameStateVersion', 'gameStateVersion'),
                ('sgtPlayerActions', 'playerActions'),
                ('sgtPlayerColors', 'playerColors'),
                ('sgtPlayerNames', 'playerNames'),
                ('sgtPlayerSeats', 'playerSeats'),
            ]
            for (sgt_name, state_name) in simple_mappings:
                if sgt_name in ble_field_order:
                    state[state_name] = values[ble_field_order.index(sgt_name)]

            players = None
            sgtPlayerActions = values[ble_field_order.index('sgtPlayerActions')].split(',') if 'sgtPlayerActions' in ble_field_order else None
            sgtPlayerColors = values[ble_field_order.index('sgtPlayerColors')].split(',') if 'sgtPlayerColors' in ble_field_order else None
            sgtPlayerNames = values[ble_field_order.index('sgtPlayerNames')].split(',') if 'sgtPlayerNames' in ble_field_order else None
            sgtPlayerSeats = values[ble_field_order.index('sgtPlayerSeats')].split(',') if 'sgtPlayerSeats' in ble_field_order else None
            nonNullPlayerArr = sgtPlayerActions or sgtPlayerColors or sgtPlayerNames or sgtPlayerSeats or None
            if (nonNullPlayerArr != None):
                players = [{} for _item in nonNullPlayerArr]
                if sgtPlayerActions:
                    for index, val in enumerate(sgtPlayerActions):
                        players[index]['action'] = val
                if sgtPlayerColors:
                    for index, val in enumerate(sgtPlayerColors):
                        players[index]['color'] = val
                if sgtPlayerNames:
                    for index, val in enumerate(sgtPlayerNames):
                        players[index]['name'] = val
                if sgtPlayerSeats:
                    for index, val in enumerate(sgtPlayerSeats):
                        players[index]['seat'] = val
                state['players'] = players
        # When was this state sent? (in monotonic space)
        ts = get_state_float(state, 'ts', 0)
        self.timestamp = ts + timestamp_offset

        # The last version of the state, used to prevent doing actions against old states. Must be sent with each command.
        self.game_state_version = get_state_int(state, 'gameStateVersion', -1)

        # Current timer-mode (cd/cu/st/nt for Count-Down/Up, SandTimer, No Timer)
        self.timer_mode = get_state_string(state, 'timerMode', GameState.TIMER_MODE_COUNT_UP)

        # The current state.
        # Sand, ru/nr/pa/en for running, not running, paused or end
        # Not Sand, st/en/pa/ad/pl for start, end, pause, admin or playing
        self.state = get_state_string(state, 'state', GameState.STATE_NOT_CONNECTED)

        # Count-Up, time taken this turn or pause time or admin time
        # Count-Down, same as above, but negative values during Delay Time
        # Sand, time taken out of the sand timer
        self.turn_time_sec = get_state_int(state, 'turnTime')

        self.player_time_sec = get_state_int(state, 'playerTime')

        # Count-Up/Down, total play time, not counting this turn and not admin/pause time
        self.total_play_time_sec = get_state_int(state, 'totalPlayTime')

        # (not sand) The current or next-up player name
        self.name = get_state_string(state, 'name', "(no name)")

        # (not sand) The current or next-up player color
        color_hex = get_state_string(state, 'color')
        self.color = ((int(color_hex[0:2],16),int(color_hex[2:4],16),int(color_hex[4:6],16))) if len(color_hex) == 6 else (255,255,255)
        self.color_simplified = simplify_color(self.color)

        # Different actions. Either None or a string starting with 'game/{action}' that
        # can be sent to the MQTT commands queue to issue commands
        actions = state['actions'] if 'actions' in state and state['actions'] != None else {}
        self.action_primary = get_action_string(actions, 'primary')
        self.action_secondary = get_action_string(actions, 'secondary')
        self.action_admin = get_action_string(actions, 'admin')
        self.action_pause = get_action_string(actions, 'pause')

        self.players = state['players'] if 'players' in state else []

    def has_action(self, action):
        return self.action_admin == action or self.action_pause == action or self.action_primary == action or self.action_secondary == action

    def __repr__(self):
        facts = []
        if (self.timestamp):
            facts.append(f'ts={self.timestamp}')
        if (self.game_state_version):
            facts.append(f'v={self.game_state_version}')
        if (self.timer_mode):
            facts.append(f'mode={self.timer_mode}')
        if (self.state):
            facts.append(f'state={self.state}')
        if (self.turn_time_sec):
            facts.append(f'turn_time={self.turn_time_sec}')
        if (self.player_time_sec):
            facts.append(f'player_time={self.player_time_sec}')
        if (self.total_play_time_sec):
            facts.append(f'total_time={self.total_play_time_sec}')
        if (self.name):
            facts.append(f'name={self.name}')
        if (self.color):
            facts.append(f'color={self.color}')
        if (self.action_primary):
            facts.append(f'a_primary={self.action_primary}')
        if (self.action_secondary):
            facts.append(f'a_secondary={self.action_secondary}')
        if (self.action_admin):
            facts.append(f'a_admin={self.action_admin}')
        if (self.action_pause):
            facts.append(f'a_pause={self.action_pause}')
        if (self.players):
            facts.append(f'players={self.players}')
        return f"<SGT State: {', '.join(facts)}>"