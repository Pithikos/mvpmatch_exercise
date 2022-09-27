# Quickstart


Install dependencies

    virtualenv .env -p python3
    source .env/bin/activate && pip install -r requirements.txt

Run locally

    python manager.py runserver_plus --nopin


# Testing

Run all tests

    pytest


# Notes/Refactoring

  - Decide on standard format for all API responses + test that
  - Simplify logic; allow both buyers and sellers for same actions if they have the money
  - Remove redundant endpoints like /deposit
  - Use factoryboy instead of custom fixtures
