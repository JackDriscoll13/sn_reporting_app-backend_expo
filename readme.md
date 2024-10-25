To read more about how this api fits into our data app, please visit [jackdriscoll.io](https://jackdriscoll.io). (Add link to project demo)

Note: I've obtained permission from my team at Spectrum to share this code on GitHub. I've been careful to exclude sensitive business logic and any confidential configuration information. This expo represents only a small slice of the greater project. Please keep that in mind if any components appear to be missing from the codebase.

### Overview

This an expo of some of the code I wrote for a project in the Spring and Summer of 2024. 

It is a REST API built in python with fastapi. 

The API sits in between a database and a frontend built in typescript, the frontend code can be found [here](https://github.com/JackDriscoll13/sn_reporting_app-frontend_expo). The application on a whole is a full stack data application that allows stakeholders to understand and report on viewership data related to Spectrum News and it's competitors. 

This code comes from an old commit and only contains logic for about 1/3 of the features currently active in the app.


### Features present in this expo:

**Authentication**
  - I rolled my own custom auth for this app
  - The auth logic is present in this codebase, the endpoints start [/app/api/endpoints/auth_api](/app/api/endpoints/auth_api.py)
  

  - User Registration and Verification: Users can register by providing their email and password. A verification code is sent to the user's email to complete the registration process.

  - Login: Users can log in using their email and password. A JWT token is generated upon successful login

  - Password Recovery: Users can request a password reset, which sends a secure token to their email to reset their password.

**Coverage Map**
- at [app/api/endpoints/coveragemap_api](app/api/endpoints/coveragemap_api.py)
- Data Retrieval: Provides endpoints to retrieve coverage map data from an S3 bucket, including real-time updates and data size metadata.


**Nielsen Daily Report**
- at [app/api/endpoints/nielsen_api](app/api/endpoints/nielsen_api.py)
- File Verification and Report Generation: Verifies uploaded Nielsen files and generates reports based on daily and benchmark data. Supports downloading of generated reports.
  
  - Meat of this report is [transformations/nielsen/nielsen_daily_report.py](/app/transformations/nielsen/nielsen_daily_report.py)
  

- Configuration and Data Management: Manages subject lines, email recipients, and DMA lists in the database, allowing updates and retrievals.

**Engagement**
- at [app/api/endpoints/engagement_api](app/api/endpoints/engagement_api.py)
- Data Range and Analytics: Offers endpoints to retrieve engagement data range and detailed analytics, including yearly and quarterly engagement data.
- Intensive pandas processing 

**Basic User Administration**
- at [app/api/endpoints/useradmin_api](app/api/endpoints/useradmin_api.py)
- User and Role Management: Provides endpoints to manage user roles, delete users, and handle pre-approved email lists.
