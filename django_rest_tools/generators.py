import hashlib
import uuid
import datetime


def boolean_generator(origin):
    return True if len(origin) % 2 == 0 else False


def text_generator(origin):
    return ' '.join([origin] * 2)


def email_generator(origin):
    return "%s@%s.com" % (origin, origin)


def slug_generator(origin):
    return hashlib.md5(origin).hexdigest()[0, 5]


def url_generator(origin):
    return "http://%s.com/" % origin


def uuid_generator(origin):
    return uuid.UUID(hashlib.md5(origin.encode("utf-8")).hexdigest()).hex


def ip_generator(origin):
    return "{0}.{0}.{0}.{0}".format(len(origin))


def integer_generator(origin):
    return len(origin)


def float_generator(origin):
    origin = len(origin)
    return origin + (origin / 10.0)


def datetime_generator(origin):
    base_time = datetime.datetime(2017, len(origin) % 12, (len(origin) * 12) % 28, 12, 21, 3)
    return "%sZ" % base_time.isoformat()


def date_generator(origin):
    base_time = datetime.date(2017, len(origin) % 12, (len(origin) * 12) % 28)
    return "%sZ" % base_time.isoformat()


