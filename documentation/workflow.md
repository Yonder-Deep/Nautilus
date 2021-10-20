# Workflow

This page details the three stage testing process at Yonder Deep.

| Phase           | Purpose                                                | Branch            |
|-----------------|--------------------------------------------------------|-------------------|
| Alpha           | local development and testing for one particular issue | varies            |
| Beta            | integration testing for feature complete code          | development       |
| Production      | fully functional code that has been thoroughly tested  | master            |

## Stage 1 - *Alpha*
Alpha testing refers to local develoment by a sub-section of the team for a particular issue. This development is done on its own branch and should be tested
with an AUV and Basestation radio connection before being merged with the development branch.
### Procedure:
#### Create a Ticket
1. Navigate to the [Issues](https://github.com/Yonder-Deep/Nautilus/issues) page and create a **New Issue** with a relevant title and description.

2. Add your issue to the Github Project [board](https://github.com/Yonder-Deep/Nautilus/projects/3) by dragging it from the "Add cards" panel.

#### Working on a Ticket
1. To start working on a ticket, create a local branch from `main`. Titling of branch names should follow this format:  
    `<Ticket Number>/<Title Abbreviation>`  
 
    You can get the ticket number from the Github issue page. An example branch name would be: `1/first-ticket`. To create the branch, make sure you are in the `main` branch and then use `git checkout -b <BRANCH NAME>`.

2. Work on your ticket within your branch, make occasional pulls and merges from main to make sure your code works with the latest changes:
    ```
    git checkout develop
    git pull
    git checkout <YOUR BRANCH>
    git merge develop
    ```
3. Add and commit changes when appropriate:
   ```
   git add <FILE>
   git commit -m "COMMIT MESSAGE"
   ```
   Commit messages should be present imperative. Example: "Add support for data transfer"
4. Push your changes to Github:
   ```
   git push
   ```
   If you are pushing your branch to Github for the first time, you will have to do this instead:
   ```
   git push --set-upstream origin <BRANCH NAME>
   ```
 
 #### Submitting a Pull Request
 1. On Github, go to "Pull requests" and create a new pull request by selecting your branch for the ticket.
 2. In the description of the pull request webpage, add:
    
    `Closes #<Issue Number>`
 3. **Make sure** you select develop as the branch being merged to.
 4. After having your PR reviewed, merge with the develop branch. 

## Stage 2 - *Beta*
Beta refers to testing conducted on a subset of features that need to be tested with a fully set-up AUV and Basestation. This will most likely consist of a pool
test or something of a similar calibar. These tests are to be conducted periodically (dates TBD).

## Stage 3 - *Production*
Production refers to the stable and fully tested code base. This code should only be updated after features on the develop branch thoroughly work as expected.
