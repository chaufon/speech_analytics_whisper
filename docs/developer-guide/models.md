# Models

This page provides information about the data models used in the Speech Analytics application.

## Overview

The Speech Analytics application uses several Django models to represent the data in the system. These models are defined in the `apps` directory, organized by application.

## User Models

### User

The User model extends Django's AbstractUser and includes additional fields for document type, document number, role, and campaign.

### Role

The Role model defines the permissions for users in the system. It includes various permission flags that control what actions a user can perform, as well as scope attributes that control what data a user can access.

For detailed information about the scope attribute, see the [Scopes](../user-guide/scopes.md) page.

### Campaign

The Campaign model represents a campaign in the system. Each user belongs to a campaign, and the campaign is used to determine what data the user can access based on their role's scope settings.

## Analytics Models

### Process

The Process model represents a process in the system. A process is a collection of audio files that are transcribed and analyzed.

### Audio

The Audio model represents an audio file in the system. Each audio file belongs to a process and is associated with an agent and a date.

### Agent

The Agent model represents an agent in the system. Agents are associated with campaigns and are used to organize audio files.

### WordList

The WordList model represents a list of words in the system. Word lists are used in the transcription and analysis of audio files.

### Typification

The Typification model represents a typification in the system. Typifications are used to categorize the results of audio analysis.

## Model Relationships

The models in the Speech Analytics application are related in various ways:

- Users belong to Campaigns and have Roles
- Processes belong to Campaigns and have WordLists and Typifications
- Audio files belong to Processes and have Agents
- Agents belong to Campaigns
