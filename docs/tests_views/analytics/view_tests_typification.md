# Overview

This Django web system relies heavily on a package named **"maintenance"**. All views and models inherit from base classes provided by that package.

# Objective

I want to create success and failure tests for the views associated with every typification-related URL
(using the `Tipification` model) that are connected to the following API_ACTIONS:


## API Action: `API_ACTION_ADD`
- Allows adding a new Typification object.
- Only users with a role that has `can_add_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action.

### GET
- Returns a modal HTML with an empty form to create a new Typification object.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_HOME`
- Show the main HTML webpage associated with model Typification
- Users with a role that has the `can_list_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action.

### GET
- Returns a webpage HTML. Validate template used.


## API Action: `API_ACTION_EDIT`
- Allows editing an existent Typification object.
- Users with a role that has the `can_edit_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns a modal HTML with a populated form with some attributes from a Typification object selected

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent Typification object.
- Users with a role that has the `can_delete_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action
- All Pattern objects associated with a selected Typification object are also soft-deleted.

### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a soft-deleted Typification object.
- Users with a role that has the `can_delete_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action
- All Pattern objects associated with a selected Typification object are also reactivated.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_READ`
- Allows seeing details of an existent Typification object when a User has no permission to edit.
- Users with a role that has the `can_list_typification` and does not have `can_edit_typification` are able to perform this action.
Also needs scope `SCOPE_CAMPAIGN`.

### GET
- Returns a modal HTML with a populated form with some attributes from a Typification object selected


## API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Typification object, even when soft-deleted.
- Users with a role that has the `can_history_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns a modal HTML with an accordion with accordion-items for every time a Typification object selected has been modified.


## API Action: `API_ACTION_LIST`
- Allows listing Typification objects, even soft-deleted ones.
- Users with a role that has the `can_list_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns an HTML table with a row per every Typification object.
- Table response is paginated
- If no Typification objects return an empty table


## API Action: `API_ACTION_RESET`
- This action is not allowed for this model.


## API Action: `API_ACTION_EXPORT_INDIVIDUAL`
- Allows downloading an Excel file (xlsx) with a list of all Pattern objects associated with a selected Typification object
- Users with a role that has the `can_export_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action
- There is a column named "Oración" which can be used to validate data from the downloaded Excel file

### GET
- Downloads an Excel file with Pattern objects per every row.


## API Action: `API_ACTION_IMPORT`
- Allows creating Pattern objects with a new Typification parent object using a xlsx file uploaded. Not updating or deleting allowed, just creation.
- Users with a role that has the `can_import_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action
- New Pattern and Typification objects created will belong to the campaign of the creator.
- Excel file will have a column named "sentence"

### GET
- Returns a modal Form to upload an Excel file and an input to set new Typification's name.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_RELATED`
- It is not a specific action, it is used to perform actions over child Pattern objects from a parent Typification object.
- Only some actions are allowed.
- The next actions are related to the Pattern model and only apply when a Typification object parent is active and not running.

### API Action: `API_ACTION_ADD`
- Allows adding a new Pattern object related to its Typification parent object
- Only users with a role that has `can_add_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action.

#### GET
- Returns a modal HTML with an empty form to create a new Pattern object.

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


### API Action: `API_ACTION_EDIT`
- Allows editing an existent Pattern object related to its Typification parent object
- Users with a role that has the `can_edit_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### GET
- Returns a modal HTML with a populated form with some attributes from a Pattern object selected

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


### API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent Pattern object related to its Typification parent object
- Users with a role that has the `can_delete_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


### API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a soft-deleted Pattern object related to its Typification parent object
- Users with a role that has the `can_delete_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


### API Action: `API_ACTION_READ`
- Allows watching details of an existent Pattern object, related to its Typification parent object, when a User has no permission to edit.
- Users with a role that has the `can_list_typification` and does not have `can_edit_typification` are able to perform this action.
Also needs scope `SCOPE_CAMPAIGN`.

#### GET
- Returns a modal HTML with a populated form with some attributes from a Pattern object selected


### API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Pattern object, related to its Typification parent object, even when soft-deleted.
- Users with a role that has the `can_history_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### GET
- Returns a modal HTML with an accordion with accordion-items for every time a Pattern object selected has been modified.


### API Action: `API_ACTION_LIST`
- Allows listing Pattern objects related to its Typification parent object, even soft-deleted ones.
- Users with a role that has the `can_list_typification` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### GET
- Returns an HTML table with a row per every Pattern object.
- Table response is not paginated
- If no Typification objects return an empty table


# Considerations

* There are fixtures for users, roles and campaigns — some of which are related to validations.
Include fixtures, but do not use those objects, create new ones to test.
* Every role has user permissions and one `scope_typification` attributes. Typification model only uses 
SCOPE_NONE and SCOPE_CAMPAIGN.
* Tests for the Wordlist model are already implemented, you can use it as a reference but create a different test file.
* Readonly users generally only have the `can_history_typification` attribute activated, thus activate the `can_list_typification` property.
* If not POST or GET listed for a specific action, include test to those http methods and check for 4XX answers
