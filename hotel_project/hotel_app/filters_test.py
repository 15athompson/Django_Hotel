import unittest
from unittest.mock import MagicMock
from django.test import TestCase
from django_filters import FilterSet
from hotel_app.filters import GuestFilter
from hotel_app.models import Guest

class TestGuestFilter(TestCase):
    
    def setUp(self):
        # Mocking the Guest model
        self.guest1 = Guest(last_name='Smith', postcode='12345')
        self.guest2 = Guest(last_name='Johnson', postcode='67890')
        self.guest3 = Guest(last_name='smith', postcode='123')
        self.guests = [self.guest1, self.guest2, self.guest3]
        Guest.objects = MagicMock()
        Guest.objects.all.return_value = self.guests

    # Test Scenario 1: Test if GuestFilter is a subclass of django_filters.FilterSet.
    def test_guest_filter_is_subclass_of_filterset(self):
        self.assertTrue(issubclass(GuestFilter, FilterSet))

    # Test Scenario 2: Test filtering guests by last name using a case-insensitive search.
    def test_filter_guests_by_last_name_case_insensitive(self):
        filter_instance = GuestFilter({'last_name': 'smith'}, queryset=Guest.objects.all())
        filtered_guests = filter_instance.qs
        self.assertIn(self.guest1, filtered_guests)
        self.assertIn(self.guest3, filtered_guests)
        self.assertNotIn(self.guest2, filtered_guests)

    # Test Scenario 3: Test filtering guests by postcode using partial matches.
    def test_filter_guests_by_postcode_partial_match(self):
        filter_instance = GuestFilter({'postcode': '123'}, queryset=Guest.objects.all())
        filtered_guests = filter_instance.qs
        self.assertIn(self.guest1, filtered_guests)
        self.assertIn(self.guest3, filtered_guests)
        self.assertNotIn(self.guest2, filtered_guests)

    # Test Scenario 4: Test if the GuestFilter class correctly sets the model to Guest and includes the fields 'last_name' and 'postcode' in the Meta class.
    def test_guest_filter_meta_class(self):
        self.assertEqual(GuestFilter.Meta.model, Guest)
        self.assertListEqual(GuestFilter.Meta.fields, ['last_name', 'postcode'])

    # Test Scenario 5: Test if the GuestFilter correctly filters guests based on the last name and postcode fields.
    def test_guest_filter_correctly_filters_by_last_name_and_postcode(self):
        filter_instance = GuestFilter({'last_name': 'smith', 'postcode': '123'}, queryset=Guest.objects.all())
        filtered_guests = filter_instance.qs
        self.assertIn(self.guest1, filtered_guests)
        self.assertIn(self.guest3, filtered_guests)
        self.assertNotIn(self.guest2, filtered_guests)

    # Test Scenario 6: Test if the 'fields' property in the GuestFilter class correctly includes 'last_name' and 'postcode'.
    def test_guest_filter_fields_property(self):
        self.assertIn('last_name', GuestFilter.Meta.fields)
        self.assertIn('postcode', GuestFilter.Meta.fields)

if __name__ == '__main__':
    unittest.main()