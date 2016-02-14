from unichan import g
from unichan.database import get_db
from unichan.lib import ArgumentError
from unichan.lib.models import Ban
from unichan.lib.proxy_request import get_ip4
from unichan.lib.utils import now


class BanService:
    def __init__(self):
        pass

    def is_request_banned(self, board=None):
        ip4 = self.get_request_ip4()
        bans = self.find_bans(ip4)
        return len(bans) > 0

    def get_request_bans(self):
        ip4 = self.get_request_ip4()
        return self.find_bans(ip4)

    def get_request_ip4(self):
        try:
            ip4 = self.parse_ip4(get_ip4())
        except ValueError:
            g.logger.exception('Failed to parse request ip4')
            raise ArgumentError('Invalid request')
        return ip4

    def find_bans(self, ip4):
        db = get_db()
        bans = db.query(Ban).filter((Ban.ip4 == ip4) | ((Ban.ip4 <= ip4) & (Ban.ip4_end >= ip4))).all()
        applied_bans = []
        for ban in bans:
            if not self.ban_valid(ban):
                self.delete_ban(ban)
            elif self.ban_applies(ban, ip4):
                applied_bans.append(ban)
        return applied_bans

    def ban_applies(self, ban, ip4):
        if ban.ip4_end is not None:
            return ban.ip4 < ip4 < ban.ip4_end
        else:
            return ban.ip4 == ip4

    def ban_valid(self, ban):
        if ban.length == 0:
            return True
        return now() <= ban.date + ban.length

    def add_ban(self, ban):
        db = get_db()
        db.add(ban)
        db.commit()

    def delete_ban(self, ban):
        db = get_db()
        db.delete(ban)
        db.commit()

    def get_all_bans(self):
        db = get_db()
        return db.query(Ban).all()

    def parse_ip4(self, ip4_str):
        ip_parts = ip4_str.split('.')
        if len(ip_parts) != 4:
            raise ValueError()

        ip_nums = []
        for ip_part in ip_parts:
            if ip_part == '*':
                ip_nums.append(0)
            else:
                n = int(ip_part)
                if n < 0 or n > 255:
                    raise ValueError()
                ip_nums.append(n)

        return (ip_nums[0] << 24) + (ip_nums[1] << 16) + (ip_nums[2] << 8) + ip_nums[3]

    def ip4_to_str(self, ip4):
        outputs = []
        for i in range(4):
            n = (ip4 >> (3 - i) * 8) & 255
            outputs.append(str(n))

        return '.'.join(outputs)
