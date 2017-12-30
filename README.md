# sports-pools-REST-API
Python Flask-RESTful API connecting to NHL and NBA standings to build JSON output for supporting web apps

v.1.1

POST ability for members, member's teams choices

SECURITY TOKENS using itsdangerous 

API KEY can be obtained by emailing me at d@drewsoske.com

--2 Step

----/api/auth POST key TO OBTAIN TOKEN (secret stored in separate file not included on Git)

	----Other Routes SEND key, token WITH EVERY REQUEST 

REFACTORING

Functions Optimized for both sports and accomodate more 

========

v.1

DESCRIPTION

This is a API that delivers a JSON object to a supporting Django web app.
Each sport has it's teams broken out into groups/regions/other
Each member choses one team from each group/region/other
UI for members to chose teams will be available shortly 


GET functions

NHL_BUILD: /nhl/build/{json | html}/{all | <member_id>}

NBA_BUILD: /nhl/build/{json | html}/{all | <member_id>}


PUT functions

Coming Soon


BUGS

Logs not working as intended

INSTALL
See setup.py for PIP installation

DATABASE
sqlite3
Database has sample data already in it to get you up and running 
members
members_teams
sports
sports_columns
sports_columns_teams
teams
