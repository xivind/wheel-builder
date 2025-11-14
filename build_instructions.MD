# Instructions for Claude Code to build wheel builder web application
This file contains instructions for Claude Code to guide the building of the wheel builder web application.

# Purpose of the wheel builder web application
The purpose of the wheel builder web application is to help users to build bicycle wheels. The program will let users select what kind of parts they are using for their wheels and what kind of wheel they are building: spoke type, hub make and model, rim make and model, nipples, and lacing (number of crosses) and number of spokes. Based on this the program will calculate what tension is recommended (min and max) on the PartkTool Tensionmeter. It will also recommend spoke lengths for right and left side. The user will be given the option to enter what spoke lengths are acutally used left and right, as well as providing a name for the wheel build, along with comments. During the build process and when the build process is done, the user will have the option to enter tension readings for each spoke and see this visualized in a table and diagram. See the build_details.html page for an example of how this could look like. It does not need to look exactly like this, its only for inspiration. But the suggestion from Claude should cover the same information, and more information, if Claude has more ideas.

When accessing the application, the user should first be shown a landing page. This page should use tiles / cards and show all the wheels build. Upon clicking on any tile, the user will be directed to the relevant build_details.html page (see above). From the landing page it should also be possible to create a new weel build. See dashboard.html for inspiration and an example on how the lading page could look like. It does not need to look exactly like this, its only for inspiration.

In order for the program to work it need a lot of rather complex formulas and info about materials. Formulas should be in the program logic, but the user should be able to enter information about rims, spokes, hubs and so on from a configuration. See config.html for an example of what this could look like.

# Tech stack
- The web application should be responsive design, so it also works on mobile phones
- FastAPI should be used for the backend
- Bootstrap should be used for the frontend
- Vanilla js should be used whenever js is needed. All js should be placed in the same js file, not placed inline in different html pages
- TomSelect should be used for advanced input boxes, and if thats not needed use standard bootstrap and html input boxes
- Date and time picker should use Tempus Domino js library
- Squlite should be used as the database
- PeeWee ORM should be used to interact with the sqlite database

# Architectural constraints
## General constraints
- main.py contains the router and should contain no business logic
- business_logic.py contains all business logic, calculations etc. Whenever CRUD operations are needed in the database, methods should always call database_manager.py and use the methods defined there. CRUD operations shall never be called directly from the business_logic module
- database_manager.py contains all methods necessary to do CRUD operations in the database
- database_model.py contains the model for the sqlite database
- logger.py contains the logging configuration. All logging, both from fastapi and python, should be done in a uniform manner and logged to the docker container. See the Dockerfile for inspiration
- seed_data.py is used to populate the database with configuration data for wheel materials on container creation
- utils.py contains helper methods, such as method to create UUIDs and other stuff that has the characteristics of being helper method

## Database configuration
- The database configuration itself should be kept as simple as possible. Do not use backrefs or automatically generated IDs. Instead, always create uniue ids for records in the backend and submit that to the database. 