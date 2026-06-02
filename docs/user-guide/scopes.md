# Understanding Scopes in Role Permissions

## What are Scopes?

In the Speech Analytics application, **scopes** are an important attribute of the Role model that determine the visibility and access level for different models in the system. Scopes define the range of data that a user with a particular role can access and manipulate.

Scopes are used to restrict or expand a user's access to data based on their role and relationship to the data. This is particularly important in a multi-tenant system where different users may need different levels of access to the same types of data.

## Scope Options

The Role model includes several scope attributes for different models in the system. Each scope attribute can have one of the following values:

| Scope Value | Constant | Description |
|-------------|----------|-------------|
| None | `SCOPE_NONE` | No access to any data of this type |
| User | `SCOPE_USER` | Access only to data created by the current user |
| Campaign | `SCOPE_CAMPAIGN` | Access to all data within the user's campaign |
| Global | `SCOPE_GLOBAL` | Access to all data across all campaigns |

These scope values are defined in the `get_scopes()` function in `apps/analytics/utils.py`:

```python
def get_scopes(allow_user=True, allow_global=True) -> dict[int, str]:
    scopes = {SCOPE_NONE: "Ninguno"}
    if allow_user:
        scopes.update({SCOPE_USER: "Solo los creados por el usuario"})
    scopes.update({SCOPE_CAMPAIGN: "Los de la campaña"})
    if allow_global:
        scopes.update({SCOPE_GLOBAL: "De todas las campañas"})
    return scopes
```

## Scope Attributes in the Role Model

The Role model includes several scope attributes, each controlling access to a different model in the system:

| Attribute | Controls Access To |
|-----------|-------------------|
| `scope_processresult` | Process results |
| `scope_process` | Processes |
| `scope_typification` | Typifications |
| `scope_wordlist` | Word lists |
| `scope_agent` | Agents |
| `scope_user` | Users |

Some models don't have an explicit scope attribute in the Role model, but instead have a property that returns a fixed scope value:

| Property | Returns | Description |
|----------|---------|-------------|
| `scope_campaign` | `SCOPE_GLOBAL` | Always returns global scope for campaigns |
| `scope_role` | `SCOPE_GLOBAL` | Always returns global scope for roles |

## How Scopes Affect Permissions

Scopes work in conjunction with permission flags (like `can_add_process`, `can_edit_process`, etc.) to determine what actions a user can perform on different objects in the system.

The `eval_perm()` method in the User model evaluates whether a user has permission to perform a specific action on a specific object, taking into account both the permission flags and the scope:

```python
def eval_perm(self, action: str, model_name: str, object_to_edit) -> bool:
    # Special case for resetting own password
    if (
        object_to_edit
        and isinstance(object_to_edit, User)
        and object_to_edit == self
        and action == API_ACTION_RESET
    ):
        return True  # reset own password always allowed

    scope = self.role.get_scope(model_name)
    if scope == SCOPE_NONE:
        return False

    has_perm = self.role.has_perm(action, model_name)
    if (
        action in (API_ACTION_ADD, API_ACTION_EXPORT, API_ACTION_HOME, API_ACTION_LIST)
        or not object_to_edit
    ):
        return has_perm

    if scope == SCOPE_USER:
        create_user = getattr(object_to_edit, "create_user", None)
        if not create_user:
            raise ValidationError("Se requiere 'create_user' en object_to_edit para SCOPE_USER")
        return create_user == self and has_perm
    elif scope == SCOPE_CAMPAIGN:
        return object_to_edit.campaign == self.campaign and has_perm
    else:  # scope == GLOBAL
        return has_perm
```

## Examples

Here are some examples of how scopes affect user permissions:

### Example 1: User with SCOPE_NONE for processes

If a user's role has `scope_process = SCOPE_NONE`, they will not be able to access any processes in the system, regardless of their other permissions.

### Example 2: User with SCOPE_USER for processes

If a user's role has `scope_process = SCOPE_USER` and `can_edit_process = True`, they will only be able to edit processes that they created themselves.

### Example 3: User with SCOPE_CAMPAIGN for processes

If a user's role has `scope_process = SCOPE_CAMPAIGN` and `can_edit_process = True`, they will be able to edit any process within their campaign, regardless of who created it.

### Example 4: User with SCOPE_GLOBAL for processes

If a user's role has `scope_process = SCOPE_GLOBAL` and `can_edit_process = True`, they will be able to edit any process in the system, regardless of which campaign it belongs to.

## Special Cases

Some models have special handling for scopes:

- For the `audio` model, the scope is determined by the `process` model's scope.
- For the `word` model, the scope is determined by the `wordlist` model's scope.
- For the `pattern` model, the scope is determined by the `typification` model's scope.

This is handled in the `get_scope()` method of the Role model:

```python
def get_scope(self, model_name: str) -> int:
    if model_name == "audio":
        model_name = "process"
    elif model_name == "word":
        model_name = "wordlist"
    elif model_name == "pattern":
        model_name = "typification"
    return getattr(self, f"scope_{model_name}", SCOPE_NONE)
```

## Conclusion

Understanding scopes is crucial for properly configuring user roles and permissions in the Speech Analytics application. By setting appropriate scope values for different models, administrators can ensure that users have access to the data they need while maintaining proper security and data isolation.
