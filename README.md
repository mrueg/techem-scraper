# techem-scraper

## Purpose
Scrapes water/heating consumption data ("Verbrauchsinfo") from mieter.techem.de.

## Background

Techem offers a portal to show the "Verbrauchsinfo" to tenants to inform them about their energy consumption.
The "Verbrauchsinfo" is a monthly generated usage report for heating and cooling as well as cold and warm water.

If you live in a multi-tenant building, Techem might be the provider for water and heating meters. 

> [!WARNING]
> Unfortunately Techem does not offer an API client, so this is an experimental way of fetching it programmatically.
> This project is not affiliated with Techem in any shape or form.
> The backend might change any time, so use at your own risk.


## --help
```
usage: techem.py [-h] [-B] [-u USERNAME] [-p PASSWORD]

Scrapes consumption data (Verbrauchsinfo) from Techem website

options:
  -h, --help            show this help message and exit
  -B, --browser
  -u, --username USERNAME
  -p, --password PASSWORD
```

## How to use

Have Python 3.x and the [MSAL](https://github.com/AzureAD/microsoft-authentication-library-for-python) python library installed.

Either, you provide your login to the script, which will then use selenium and chrome headless to log You in:

```
./techem-eed-scraper.py -u email@example.com -p mysecurepassword
```

or You need to be logged out of the mieter.techem.de portal in your browser (no active session) and run

``` 
./techem.py -B
``` 

## How it works

The portal mieter.techem.de manages user logins via [Azure Active Directory B2C](https://azure.microsoft.com/en-us/products/active-directory-b2c).
It uses an OAuth 2.0 Auth Code Flow, for which the scraper will open a web browser for you to log in with your credentials.

After copying in the Redirect URL (starts with https://mieter.techem.de/auth?state), the script will automatically fetch your consumption data and create three types of files:

* period.json (containing the periods you have stored)
* YYYY-MM.json (containing the consumption data of the specific month)
* YYYY-MM-average.json (containing the consumption of other comparably-sized appartments

## Sample data

The data provided by the API looks like this:

```
{
    "count": 4,
    "data": [
        {
            "period": "2023-01",
            "service": "HOT_WATER",
            "unitOfMeasure": "M3",
            "amount": 1.9,
            "quality": 1.0,
            "revision": 2,
            "status": "OK",
            "createdAt": "2025-04-27T17:13:07Z"
        },
        {
            "period": "2023-01",
            "service": "HOT_WATER",
            "unitOfMeasure": "KWH",
            "amount": 223.0,
            "quality": 1.0,
            "revision": 2,
            "status": "OK",
            "createdAt": "2025-04-27T17:13:07Z"
        },
        {
            "period": "2023-01",
            "service": "HEATING",
            "unitOfMeasure": "HCU",
            "amount": 2504.0,
            "quality": 1.0,
            "revision": 2,
            "status": "OK",
            "createdAt": "2025-04-27T17:13:07Z"
        },
        {
            "period": "2023-01",
            "service": "HEATING",
            "unitOfMeasure": "KWH",
            "amount": 1912.9,
            "quality": 1.0,
            "revision": 2,
            "status": "OK",
            "createdAt": "2025-04-27T17:13:07Z"
        }
    ]
}
```

The comparable data for average looks like:

```
{
    "count": 2,
    "revision": 2,
    "data": [
        {
            "service": "HEATING",
            "unitOfMeasure": "KWH",
            "amount": 2392.92,
            "createdAt": 1677926811000,
            "status": "OK"
        },
        {
            "service": "HOT_WATER",
            "unitOfMeasure": "KWH",
            "amount": 288.911507,
            "createdAt": 1677926811000,
            "status": "OK"
        }
    ]
}
```


## Interesting findings about the backend

* Blocks user agents like python requests
* If the measurement for certain reasons is not plausible, the website won't show it. The API response shows the consumption with a status `EED_NE_BLACKLIST_IMPLAUSIBLE`.
