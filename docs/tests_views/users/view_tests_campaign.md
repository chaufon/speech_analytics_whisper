# Overview

This Django web system relies heavily on a package named **"maintenance"**.
All views and models inherit from base classes provided by that package.


# Objective
I want to create success and failure tests for the views associated with every campaign-related URL
(using the `Campaign` model) that are connected to the following API_ACTIONS:


## API Action: `API_ACTION_ADD`
- Allows adding a new Campaign object.
- Only users with a role that has `can_add_campaign` attribute are able to perform this action.
- When a new Campaign object is created, also a new Config object is also created. Validate that.

### GET
- Returns a modal HTML with an empty form to create a new Campaign object.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_HOME`
- Show the main HTML webpage associated with a Campaign model object
- Users with a role that has the `can_list_campaign` attribute are able to perform this action

### GET
- Returns a webpage HTML. Validate template used.


## API Action: `API_ACTION_EDIT`
- Allows editing an existent Campaign object.
- Users with a role that has the `can_edit_campaign` are able to perform this action

### GET
- Returns a modal HTML with a populated form with some attributes from a Campaign object selected

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent Campaign object.
- Users with a role that has the `can_delete_campaign` are able to perform this action

### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a soft-deleted Campaign object.
- Users with a role that has the `can_delete_campaign` are able to perform this action

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_READ`
- Allows seeing details of an existent Campaign object when a User has no permission to edit.
- Users with a role that has the `can_list_campaign` and does not have `can_edit_campaign` are able to perform this action

### GET
- Returns a modal HTML with a populated form with some attributes from a Campaign object selected


## API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Campaign object, even when soft-deleted.
- Users with a role that has the `can_history_campaign` are able to perform this action

### GET
- Returns a modal HTML with an accordion with accordion-items for every time a Campaign object selected was changed.


## API Action: `API_ACTION_LIST`
- Allows listing Campaign objects, even soft-deleted ones.
- Users with a role that has the `can_list_campaign` are able to perform this action

### GET
- Returns an HTML table with a row per every Campaign object.
- Table response is paginated
- If no Campaign objects return an empty table


## API Action: `API_ACTION_EXPORT`
- Allows downloading an Excel file (xlsx) with a list of all Campaign objects
- Users with a role that has the `can_export_campaign` are able to perform this action
- There is a column called "id" which can be used to validate data from Excel file download

### GET
- Downloads an Excel file with Campaign objects per every row.

# Considerations

* There are fixtures for users, roles and campaigns — some of which are related to validations.
Include fixtures, but do not use those objects, create new ones to test.
* Every role has model permissions and one `scope_xxx` (model) attributes. But for the Campaign model
there is only SCOPE_GLOBAL associated.
* Tests for the User and Role models are already implemented, you can use it as a reference but create a different test file.
* If not POST or GET listed for a specific action, include test to those http methods and check for 4XX answers
* Readonly users generally only have the `can_history_campaign` attribute activated, thus activate the `can_list_campaign` property.
