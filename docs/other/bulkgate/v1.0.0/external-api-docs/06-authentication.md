# BulkGate API — Authentication (API Administration & Tokens)

Source:
- https://help.bulkgate.com/docs/en/api-administration.html
- https://help.bulkgate.com/docs/en/api-tokens.html

## Overview

BulkGate uses Application ID + Application Token for API authentication.
Both values are obtained from the BulkGate Portal.

## How to get API access data

1. Log in to [BulkGate Portal](https://portal.bulkgate.com/)
2. Go to **Modules & APIs**
3. Choose the API you want to create and click on it
4. Click **Create API**
5. Your API has been created
6. You can now see `APPLICATION_ID` and `APPLICATION_TOKEN`

## What is Application ID?

`APPLICATION_ID` is a unique identification number which you need to access your API together with `APPLICATION_TOKEN`.

## What is an API token?

`APPLICATION_TOKEN` serves as a security measure for your API. It is a key that you need to access your API together with `APPLICATION_ID`. You should never provide it to anyone.

If you suspect someone may have access to your API, you should disable the token or add a new token.

## Token management

### Disable a token
1. Log in to BulkGate Portal
2. Go to **Modules & APIs**
3. Select the API
4. Click on **Token actions** (3 vertical dots) and click **Disable**

### Add a new token
1. Log in to BulkGate Portal
2. Go to **Modules & APIs**
3. Select the API
4. Click **Add token**
5. New token has been generated

## How to set up delivery reports

1. Log in to BulkGate Portal
2. Go to **Modules & APIs**
3. Create a new API or click on an existing one
4. In the **Delivery reports** section click on the **+** button (Activate delivery reports)
5. Enter URL address to receive delivery reports on
6. Optionally check:
   - `Bulk DLRs - bulk request` to receive delivery reports in bulk only
   - `Report only when error occurs` to receive delivery reports only when an error occurs
7. Click **Save**

## How to activate or deactivate an API

1. Log in to BulkGate Portal
2. Go to **Modules & APIs**
3. Select which API you want to activate/deactivate and click on it
4. Change the status in the right-upper corner
