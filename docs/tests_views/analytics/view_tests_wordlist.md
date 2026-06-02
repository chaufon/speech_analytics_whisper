# Overview

This Django web system relies heavily on a package named **"maintenance"**. All views and models inherit from base classes provided by that package.

# Objective

I want to create success and failure tests for the views associated with every wordlist related URL
(using the `Wordlist` model) that are connected to the following API_ACTIONS:


## API Action: `API_ACTION_ADD`
- Allows adding a new Wordlist object.
- Only users with a role that has `can_add_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action.

### GET
- Returns a modal HTML with an empty form to create a new Wordlist object.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_HOME`
- Show the main HTML webpage associated with model Wordlist
- Users with a role that has the `can_list_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action.

### GET
- Returns a webpage HTML. Validate template used.


## API Action: `API_ACTION_EDIT`
- Allows editing an existent Wordlist object.
- Users with a role that has the `can_edit_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns a modal HTML with a populated form with some attributes from a Wordlist object selected

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent Wordlist object.
- Users with a role that has the `can_delete_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action
- All Word objects associated with a selected Wordlist object are also soft-deleted.

### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a soft-deleted Wordlist object.
- Users with a role that has the `can_delete_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action
- All Word objects associated with a selected Wordlist object are also reactivated.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_READ`
- Allows seeing details of an existent Wordlist object when a User has no permission to edit.
- Users with a role that has the `can_list_wordlist` and does not have `can_edit_wordlist` are able to perform this action.
Also needs scope `SCOPE_CAMPAIGN`.

### GET
- Returns a modal HTML with a populated form with some attributes from a Wordlist object selected


## API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Wordlist object, even when soft-deleted.
- Users with a role that has the `can_history_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns a modal HTML with an accordion with accordion-items for every time a Wordlist object selected was changed.


## API Action: `API_ACTION_LIST`
- Allows listing Wordlist objects, even soft-deleted ones.
- Users with a role that has the `can_list_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action

### GET
- Returns an HTML table with a row per every Wordlist object.
- Table response is paginated
- If no Wordlist objects return an empty table


## API Action: `API_ACTION_RESET`
- This action is not allowed for this model.


## API Action: `API_ACTION_EXPORT_INDIVIDUAL`
- Allows downloading an Excel file (xlsx) with a list of all Word objects associated with a selected Wordlist object
- Users with a role that has the `can_export_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action
- There is a column named "Palabra" which can be used to validate data from a downloaded Excel file 

### GET
- Downloads an Excel file with Word objects per every row.


## API Action: `API_ACTION_IMPORT`
- Allows creating Word objects with a new Wordlist parent object using a xlsx file uploaded. Not updating or deleting allowed, just creation.
- Users with a role that has the `can_import_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action
- New Words and Wordlist objects created will belong to the campaign of the creator.
- Excel file will have a column named "word"

### GET
- Returns a modal Form to upload an Excel file and an input to set the new Wordlist's name.

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


## API Action: `API_ACTION_RELATED`
- It is not a specific action, it is used to perform actions over child Word objects from a parent Wordlist object.
- Only some actions are allowed.
- The next actions are related to the Word model and only apply when a Wordlist object parent is active and not running.

### API Action: `API_ACTION_ADD`
- Allows adding a new Word object related to its Wordlist parent object
- Only users with a role that has `can_add_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action.

#### GET
- Returns a modal HTML with an empty form to create a new Word object.

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


### API Action: `API_ACTION_EDIT`
- Allows editing an existent Word object related to its Wordlist parent object
- Users with a role that has the `can_edit_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### GET
- Returns a modal HTML with a populated form with some attributes from a Word object selected

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


### API Action: `API_ACTION_DELETE`
- Allows soft-delete an existent Word object related to its Wordlist parent object
- Users with a role that has the `can_delete_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### DELETE
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


### API Action: `API_ACTION_REACTIVATE`
- Allows re-activating a soft-deleted Word object related to its Wordlist parent object
- Users with a role that has the `can_delete_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns HTTP 204 with a failed header event.


### API Action: `API_ACTION_READ`
- Allows watching details of an existent Word object, related to its Wordlist parent object, when a User has no permission to edit.
- Users with a role that has the `can_list_wordlist` and does not have `can_edit_wordlist` are able to perform this action.
Also needs scope `SCOPE_CAMPAIGN`.

#### GET
- Returns a modal HTML with a populated form with some attributes from a Word object selected


### API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Word object, related to its Wordlist parent object, even when soft-deleted.
- Users with a role that has the `can_history_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### GET
- Returns a modal HTML with an accordion with accordion-items for every time a Word object selected was changed.


### API Action: `API_ACTION_LIST`
- Allows listing Word objects related to its Wordlist parent object, even soft-deleted ones.
- Users with a role that has the `can_list_wordlist` with scope `SCOPE_CAMPAIGN` are able to perform this action

#### GET
- Returns an HTML table with a row per every Word object.
- Table response is not paginated
- If no Wordlist objects return an empty table


# Considerations

* There are fixtures for users, roles and campaigns — some of which are related to validations.
Include fixtures, but do not use those objects, create new ones to test.
* Every role has user permissions and one `scope_wordlist` attributes.
To a Wordlist model only SCOPE_NONE and SCOPE_CAMPAIGN apply.
* Tests for the User, Role, Campaign, Config and Agent models are already implemented, you can use it as a reference but create a different test file.
* Readonly users generally only have the `can_history_wordlist` attribute activated, thus activate the `can_list_wordlist` property.
* If not POST or GET listed for a specific action, include test to those http methods and check for 4XX answers
