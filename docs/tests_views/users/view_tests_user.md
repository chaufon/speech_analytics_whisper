# Overview

This Django web system relies heavily on a package named **"maintenance"**. All views and models inherit from base classes provided by that package.

# Objective

I want to create success and failure tests for the views associated with every user-related URL
(using the `User` model) that are connected to the following API_ACTIONS:


## API Action: `API_ACTION_ADD`
- Allows adding a new User object.
- Only users with a role that has `can_add_user` attribute and `scope_user` in
(`SCOPE_CAMPAIGN`, `SCOPE_GLOBAL`) are able to perform this action.

### GET
- Returns a modal HTML with an empty form to create a new User object.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_HOME`
- Show the main HTML webpage associated with a User object
- Users with a role that has the `can_list_user` attribute and any scope but `SCOPE_NONE` are able
to perform this action

### GET
- Returns a webpage HTML. Validate template used.


## API Action: `API_ACTION_EDIT`
- Allows editing an existent User object.
- Users with a role that has the `can_edit_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can edit another User object from the same Campaign
- Users with scope `SCOPE_GLOBAL` can edit another User object from any Campaign

### GET
- Returns a modal HTML with a populated form with some attributes from a User object selected

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent User object.
- Users with a role that has the `can_delete_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can soft-delete another User object from the same Campaign
- Users with scope `SCOPE_GLOBAL` can soft-delete another User object from any Campaign

### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a soft-deleted User object.
- Users with a role that has the `can_delete_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can re-activate another User object from the same Campaign
- Users with scope `SCOPE_GLOBAL` can re-activate another User object from any Campaign

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_READ`
- Allows seeing details of an existent User object when a User has no permission to edit.
- Users with a role that has the `can_list_user` and does not have `can_edit_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can "read" another User object from the same Campaign
- Users with scope `SCOPE_GLOBAL` can "read" another User object from any Campaign

### GET
- Returns a modal HTML with a populated form with some attributes from a User object selected


## API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent User object, even when soft-deleted.
- Users with a role that has the `can_history_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can "history" another User object from the same Campaign
- Users with scope `SCOPE_GLOBAL` can "history" another User object from any Campaign

### GET
- Returns a modal HTML with an accordion with accordion-items for every time a User object selected was changed.


## API Action: `API_ACTION_LIST`
- Allows listing User objects, even soft-deleted ones.
- Users with a role that has the `can_list_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can list all User objects from the same Campaign
- Users with scope `SCOPE_GLOBAL` can list all User objects

### GET
- Returns an HTML table with a row per every User object.
- Table response is paginated
- If no User objects return an empty table


## API Action: `API_ACTION_RESET`
- Allows resetting a User object's password.
- Users with a role that has the `can_change_user_password` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can "reset" another User object from the same Campaign
- Users with scope `SCOPE_GLOBAL` can "reset" another User object from any Campaign

### GET
- Returns a modal HTML with just one input to ingress a new password.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_EXPORT`
- Allows downloading an Excel file (xlsx) with a list of all User objects
- Users with a role that has the `can_export_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can export User objects from the same Campaign
- Users with scope `SCOPE_GLOBAL` can export User objects from any Campaign
- There is a column named "id" which can be used to validate data from a downloaded Excel file

### GET
- Downloads an Excel file with User objects per every row.


## API Action: `API_ACTION_IMPORT`
- Allows creating User objects with an uploaded xlsx file. Not updating or deleting allowed, just creation.
- Users with a role that has the `can_import_user` are able to perform this action
- Users with scope in `SCOPE_CAMPAIGN` can "import" User objects to the same campaign of the user performing the action.
- Users with scope in `SCOPE_GLOBAL` can "import" User objects to any campaign except ADMIN_CAMPAIGN.

### GET
- Returns a modal Form to upload an Excel file

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


# Considerations

* There are fixtures for users, roles and campaigns — some of which are related to validations.
Include fixtures, but do not use those objects, create new ones to test.
* Every role has user permissions and one `scope_user` attributes. Include tests for every scope.
* Tests for API_ACTION_ADD are already implemented (can be used as reference). Can be modified if needed to unify methods, variables, etc.
* If not POST or GET listed for a specific action, include test to those http methods and check for 4XX answers
