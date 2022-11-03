import datetime

filename = 1
with open(str(filename), 'r', encoding='utf-8') as f:
    line = f.readline()
    t_l = datetime.datetime.strptime(line[:23], '%Y-%m-%d %H:%M:%S,%f')
    while 1:
        line = f.readline()
        if not line:
            break
        t_r = datetime.datetime.strptime(line[:23], '%Y-%m-%d %H:%M:%S,%f')
        d = t_r - t_l
        d = (d.microseconds//1000/1000) + d.seconds
        if int(d) > 5:
            print(line)
        t_l = t_r
