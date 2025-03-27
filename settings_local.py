SETTINGS = {

    'weights': "models/yolo11x.pt",
    'ip_address_netregistrator': "192.168.1.72",

    'stream_channel': {
        'fire_exit_imitif': "5",    #192.168.1.31
        'angle_imitif': "1",        #192.168.1.35
        'hallway_imitif': "7",      #192.168.1.37
        'hall_imitif': "8",         #192.168.1.38
        'street': "9",              #192.168.1.39
        'hall_igz': "6",            #192.168.1.36
        'hallway_igz': "3",         #192.168.1.34
        'angle_igz': "4",           #192.168.1.32
        'fire_exit_igz': "10",      #192.168.1.40
        '301_6k': "2",              #192.168.1.33
        '323_6k_window': "11",      #192.168.1.41
        '323_6k_door': "12"         #192.168.1.42
    },

    'stream_type': {
        'main_stream': "0",
        'sub_stream': "1"
    },

    'key_stream_channel': "301_6k",
    'key_stream_type': "sub_stream",

    'log': "admin",
    'pass': "Qwerty123",
    'port': "554",

    'view_img': "True",
    'save_img': "False",
    'exist_ok': "False",

    'classes': None,

    'line_thickness': 2,
    'track_thickness': 2,

    'resize_coeff': 1,

    'exitButton': "q"
}