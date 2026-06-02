# Roles and Permissions

This page provides information about user roles and permissions in the Speech Analytics application.

## Overview

The Speech Analytics application uses a role-based access control system to manage user permissions. Each user is assigned a role, which determines what actions they can perform in the system.

## Role Model

The Role model defines the permissions for users in the system. It includes various permission flags that control what actions a user can perform, as well as scope attributes that control what data a user can access.

For detailed information about the scope attribute, see the [Scopes](scopes.md) page.

## Permission Flags

The Role model includes numerous permission flags, each controlling a specific action on a specific model. These flags are boolean values that determine whether a user with the role can perform the action.

Examples of permission flags include:

- `can_add_process`: Controls whether a user can add new processes
- `can_edit_process`: Controls whether a user can edit existing processes
- `can_delete_process`: Controls whether a user can delete or reactivate processes
- `can_history_process`: Controls whether a user can view the history of changes to processes

## Evaluating Permissions

The `eval_perm()` method in the User model evaluates whether a user has permission to perform a specific action on a specific object, taking into account both the permission flags and the scope.

## Admin Role

The system includes a special admin role that has full permissions to all actions and data in the system. This role cannot be modified or deleted.
