import unittest
from datetime import datetime
from unittest.mock import patch

from weekly_context_export import candidate, TICKERS


class HolidayClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 10, 9, 30, tzinfo=tz)


def rows(week='2026-10-09', day='2026-10-08'):
    return [dict(ticker=str(t), weekly_asof=week, daily_asof=day,
                 **{'W Trend': '↑多', 'W Pulse': '修', 'W Loc': '中',
                    'Resonance': '○同'}) for t in TICKERS]


class WeeklyHolidayTests(unittest.TestCase):
    def generate(self, data, clock=HolidayClock):
        with patch('weekly_context_export.datetime', clock), patch(
                'weekly_context_export.build_watch_map', return_value=data):
            return candidate()

    def test_verified_friday_holiday_accepts_thursday(self):
        payload = self.generate(rows())
        self.assertEqual(payload['weekly_asof'], '2026-10-09')
        self.assertEqual(set(payload['daily_asof_by_ticker'].values()), {'2026-10-08'})

    def test_missing_thursday_for_one_stock_is_blocked(self):
        data = rows()
        data[0]['daily_asof'] = '2026-10-07'
        with self.assertRaisesRegex(ValueError, 'Daily source dates'):
            self.generate(data)

    def test_current_day_is_blocked(self):
        with self.assertRaisesRegex(ValueError, 'Daily source dates'):
            self.generate(rows(day='2026-10-10'))

    def test_prior_week_is_still_blocked(self):
        with self.assertRaisesRegex(ValueError, 'Need completed week'):
            self.generate(rows(week='2026-10-02', day='2026-10-08'))

    def test_ordinary_friday_still_requires_friday(self):
        class OrdinaryClock(HolidayClock):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 17, 9, 30, tzinfo=tz)
        with self.assertRaisesRegex(ValueError, 'Daily source dates'):
            self.generate(rows(week='2026-10-16', day='2026-10-15'), OrdinaryClock)
        self.generate(rows(week='2026-10-16', day='2026-10-16'), OrdinaryClock)

    def test_friday_does_not_admit_developing_week(self):
        class FridayClock(HolidayClock):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 9, 9, 30, tzinfo=tz)
        with self.assertRaisesRegex(ValueError, 'Need completed week'):
            self.generate(rows(), FridayClock)


if __name__ == '__main__':
    unittest.main()
