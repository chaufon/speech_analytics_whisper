# Overview

This Django web system relies heavily on a package named **"maintenance"**. All views and models inherit from base classes provided by that package.

# Objective

I want to create success and failure tests for the views associated with every config-related URL
(using the `Config` model) that are connected to the following API_ACTIONS:


## API Action: `API_ACTION_ADD`
- This action is not allowed at all.
- Config objects are created automatically when a new Campaign object is added to the system.


## API Action: `API_ACTION_HOME`
- Show the main HTML webpage associated with a Config model object
- Users with a role that has the `can_list_user` attribute and any scope but `SCOPE_NONE` are able
to perform this action. So there is only one Config object per Campaign.

### GET
- Returns a webpage HTML. Validate template used.


## API Action: `API_ACTION_EDIT`
- Allows editing an existent Config object.
- Users with a role that has the `can_edit_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can edit the Config object associated with the same Campaign
- Users with scope `SCOPE_GLOBAL` can edit the Config object associated with any Campaign

### GET
- Returns a modal HTML with a populated form with some attributes from a Config object selected

### POST
- **On success**: Returns HTTP 204 with a header event.
- **On failure**: Returns modal HTML with a form containing error messages.


## API Action: `API_ACTION_DELETE`
- This action is not allowed at all.
- Config objects are hard-deleted automatically when a new Campaign object is added to the system.


## API Action: `API_ACTION_REACTIVATE`
- This action is not allowed at all.
- Config objects are created automatically when an existent Campaign object is reactivated.


## API Action: `API_ACTION_READ`
- Allows seeing details of an existent Config model object when a User has no permission to edit.
- Users with a role that has the `can_list_user` and does not have `can_edit_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can "read" the Config object associated with the same Campaign
- Users with scope `SCOPE_GLOBAL` can "read" the Config object associated with any Campaign

### GET
- Returns a modal HTML with a populated form with some attributes from a Config object selected


## API Action: `API_ACTION_HISTORY`
- Allows seeing changes performed previously on an existent Config object, even when soft-deleted.
- Users with a role that has the `can_history_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can "history" the Config object associated with the same Campaign
- Users with scope `SCOPE_GLOBAL` can "history" the Config object associated with any Campaign

### GET
- Returns a modal HTML with an accordion with accordion-items for every time a Config object selected was changed.


## API Action: `API_ACTION_LIST`
- Allows listing Config objects, even soft-deleted ones.
- Users with a role that has the `can_list_user` are able to perform this action
- Users with scope `SCOPE_CAMPAIGN` can list the Config object associated with the same Campaign
- Users with scope `SCOPE_GLOBAL` can list the Config object associated with any Campaign

### GET
- Returns an HTML table with a row per every Config object.
- Table response is paginated
- If no Config objects return an empty table


## API Action: `API_ACTION_RESET`
- This action is not allowed at all.


## API Action: `API_ACTION_EXPORT`
- This action is not allowed at all.


## API Action: `API_ACTION_IMPORT`
- This action is not allowed at all.


# Considerations

* There are fixtures for users, roles and campaigns — some of which are related to validations.
Include fixtures, but do not use those objects, create new ones to test.
* Every role has model permissions and one `scope_xxx` (model) attributes. But for the Config model
the only options are: SCOPE_CAMPAIGN, SCOPE_GLOBAL. Include tests for every scope.
* Tests for the User, Role and Campaigns models are already implemented, you can use it as a reference but create a different test file.
* If not POST or GET listed for a specific action, include test to those http methods and check for 4XX answers
* Readonly users generally only have the `can_history_config` attribute activated, thus activate the `can_list_config` property.

