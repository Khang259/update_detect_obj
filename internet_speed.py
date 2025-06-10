import speedtest as st

def speed_test():
    test =  st.Speedtest()
    up_speed = test.upload()
    up_speed = round(up_speed / 10**6, 2)
    print(f"Upspeed:{up_speed}")

    ping =  test.results.ping
    print(f"Ping(ms):{ping}")

speed_test()