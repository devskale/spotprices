import sys
from pathlib import Path
from datetime import datetime, timedelta
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from db.models.spot_prices import Base, SpotPrice
from db.operations.update_db import find_gaps, find_missing_dates, update_db

class TestUpdateDB(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_find_gaps_empty_db(self):
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        gaps = find_gaps(self.session, start_date, end_date)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0], (start_date, end_date))

    def test_find_gaps_with_data(self):
        now = datetime.now()
        prices = [
            SpotPrice(
                start_timestamp=int((now - timedelta(hours=3)).timestamp()),
                end_timestamp=int((now - timedelta(hours=2)).timestamp()),
                price=10.0,
                unit='ct/kWh',
                source='awattar'
            ),
            SpotPrice(
                start_timestamp=int((now - timedelta(hours=1)).timestamp()),
                end_timestamp=int(now.timestamp()),
                price=12.0,
                unit='ct/kWh',
                source='awattar'
            )
        ]
        for price in prices:
            self.session.add(price)
        self.session.commit()

        start_date = now - timedelta(hours=4)
        end_date = now
        gaps = find_gaps(self.session, start_date, end_date)
        self.assertEqual(len(gaps), 2)  # Gap at start and between prices

    def test_find_missing_dates_empty_db(self):
        missing_dates = find_missing_dates(self.session)
        self.assertEqual(len(missing_dates), 1)
        self.assertEqual(missing_dates[0], datetime.now().date())

if __name__ == '__main__':
    unittest.main()