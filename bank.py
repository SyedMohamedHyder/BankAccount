from numbers import Real
from decimal import Decimal
from fractions import Fraction
from datetime import datetime, timezone, timedelta


class TransactionAbort(Exception):
    pass


class TransactionCodeError(Exception):
    pass


class TimeZone:
    def __init__(self, name, hours, minutes):
        self.name = name
        self.hours = hours
        self.minutes = minutes

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) or len(value) < 1:
            raise ValueError('Invalid name for TimeZone')
        else:
            self._name = value

    @property
    def hours(self):
        return self._hours

    @hours.setter
    def hours(self, value):
        if not isinstance(value, int) or value >= 24 or value <= -24:
            raise ValueError('Hours can only have integer values from -23 to 23')
        else:
            self._hours = value

    @property
    def minutes(self):
        return self._minutes

    @minutes.setter
    def minutes(self, value):
        if not isinstance(value, int) or value >= 60 or value <= -60:
            raise ValueError('Minutes can only have integer values from -59 to 59')
        else:
            self._minutes = value

    @property
    def offset(self):
        return timedelta(hours=self.hours, minutes=self.minutes)

    def __repr__(self):
        return f'TimeZone(name={self.name}, hours={self.hours}, minutes={self.minutes})'


class TransactionID:
    trans_num = -1

    def __init__(self, trans_code, account_num, *, utc_time=None, tz=None):
        self._codes = 'DWIX'
        self.trans_code = trans_code
        self.trans_type = self._codes[self.trans_code]
        self.account_num = account_num
        self.utc_time = utc_time or datetime.utcnow()
        self.tz = tz or timezone.utc
        self.inc_trans_num()

    @property
    def utc_time(self):
        return self._utc_time

    @utc_time.setter
    def utc_time(self, value):
        if not isinstance(value, datetime):
            self._utc_time = datetime.strptime(value, '%Y%m%d%H%M%S')
        else:
            self._utc_time = value

    @classmethod
    def inc_trans_num(cls):
        cls.trans_num += 1

    @property
    def transaction_num(self):
        formatted_dt = datetime.strftime(self.utc_time, '%Y%m%d%H%M%S')
        return f'{self.trans_type}-{self.account_num}-{formatted_dt}-{self.trans_num}'

    @property
    def time(self):
        if self.tz is timezone.utc:
            tz_time = self.utc_time
            tz_name = 'UTC'
        else:
            tz_time = self.utc_time.astimezone(self.tz)
            tz_name = tz_time.tzinfo
        return datetime.strftime(tz_time, f'%Y-%m-%d %H:%M:%S({tz_name})')

    @property
    def time_utc(self):
        return self.utc_time.isoformat()

    def __repr__(self):
        return f'TransactionID({self.transaction_num})'


class Account:
    interest_rate = 0.5

    def __init__(self, account_num, first_name, last_name, *, tz=timezone.utc, balance=0):
        self._account_num = account_num
        self.first_name = first_name
        self.last_name = last_name
        self.set_tz(tz)

        if not (isinstance(balance, Real) or isinstance(balance, Decimal)) or balance < 0:
            raise ValueError('Balance must be a non-negative real number')
        else:
            self._balance = balance

    @property
    def account_number(self):
        return self._account_num

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, name):
        if not isinstance(name, str):
            raise TypeError('Name should only be a string')
        elif len(name) < 1:
            raise ValueError('First Name should be atleast 1 character long')
        else:
            self._first_name = name.strip()

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, name):
        if not isinstance(name, str):
            raise TypeError('Name should only be a string')
        else:
            self._last_name = name.strip()

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def balance(self):
        return self._balance

    @classmethod
    def get_tz(cls):
        return cls._tz

    @classmethod
    def set_tz(cls, tz):
        if isinstance(tz, TimeZone):
            tz = timezone(tz.offset, tz.name)
        if not isinstance(tz, timezone):
            raise TypeError('Invalid TimeZone object passed')
        cls._tz = tz

    def deposit(self, value):
        if not (isinstance(value, Real) or isinstance(value, Decimal)) or value < 0:
            raise ValueError('Deposit amount must be a non-negative real number')
        else:
            self._balance += value
            return TransactionID(0, self.account_number)

    def withdraw(self, value):
        if not (isinstance(value, Real) or isinstance(value, Decimal)) or value < 0:
            raise ValueError('Withdrawal amount must be a non-negative real number')
        elif self._balance - value < 0:
            raise TransactionAbort(f'Insufficient balance: {TransactionID(3, self.account_number)}')
        else:
            self._balance -= value
            return TransactionID(1, self.account_number)

    def pay_monthly_interest(self):
        interest_amount = self.balance * (self.interest_rate / 100)
        self._balance += interest_amount
        return TransactionID(2, self.account_number)

    @classmethod
    def parse_confirmation_code(cls, confirmation_num):
        trans_type, account_num, utc_time, trans_num = confirmation_num.split('-')
        if trans_type not in 'DWIX':
            raise TransactionCodeError('Invalid Transaction Code')
        trans_code = 'DWIX'.index(trans_type)
        trans_id = TransactionID(trans_code, int(account_num), utc_time=utc_time, tz=cls.get_tz())
        trans_id.trans_num = int(trans_num)
        return trans_id

    def __repr__(self):
        return f'Account(name={self.full_name}, balance={self.balance})'