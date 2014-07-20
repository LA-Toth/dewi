def add_frame(s: str):
        lines = s.split('\n')
        res = '#' * 70
        res += '\n'
        for line in lines:
                res += '# %s\n' % (line,)

        res += '#' * 70
        res += '\n'
        return res


def humanize_time(seconds, format=False):
    (minutes, seconds) = divmod(seconds, 60)
    (hours, minutes) = divmod(minutes, 60)
    days = 0
    if hours > 24:
        (days, hours) = divmod(hours, 24)
    if format:
        result = ''
        if days > 0:
            result = '%d days ' % days
        result = '%s%02d:%02d:%05.2f' % (result, hours, minutes, seconds)
        return result
    return (days, hours, minutes, seconds)
