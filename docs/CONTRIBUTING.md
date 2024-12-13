# Contributing Guide

Thank you for investing your time in contributing to our project! Any contribution you make will be greatly appreciated.

Read our [Code of Conduct](./CODE_OF_CONDUCT.md) to keep our community approachable and respectable.

In this guide, you will get an overview of the contribution workflow from opening an issue, creating a PR, reviewing, and merging the PR.

## New Contributor Guide

To get an overview of the project, read the [README](./README.md) file. Here are some resources to help you get started with open source contributions:

- [Finding ways to contribute to open source on GitHub](https://docs.github.com/en/get-started/exploring-projects-on-github/finding-ways-to-contribute-to-open-source-on-github)
- [Set up Git](https://docs.github.com/en/get-started/getting-started-with-git/set-up-git)
- [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)

## Getting Started

To navigate our codebase with confidence, see [the introduction to working in the docs repository](../docs/README.md). For more information on how we write our markdown files, see "[Using Markdown and Liquid in GitHub Docs](https://docs.github.com/en/contributing/writing-for-github-docs/using-markdown-and-liquid-in-github-docs)."

Check to see what [types of contributions](../docs/types-of-contributions.md) we accept before making changes. Some of them don't even require writing a single line of code.

### Issues

#### Create a New Issue

If you spot a problem with the docs, [search if an issue already exists](https://docs.github.com/en/github/searching-for-information-on-github/searching-on-github/searching-issues-and-pull-requests#search-by-the-title-body-or-comments). If a related issue doesn't exist, you can open a new issue using a relevant [issue form](https://github.com/github/docs/issues/new/choose).

#### Solve an Issue

Scan through our [existing issues](https://github.com/github/docs/issues) to find one that interests you. You can narrow down the search using `labels` as filters. See "[Label reference](https://docs.github.com/en/contributing/collaborating-on-github-docs/label-reference)" for more information. As a general rule, we don’t assign issues to anyone. If you find an issue to work on, you are welcome to open a PR with a fix.

### Make Changes

#### Make Changes in the UI

Click **Make a contribution** at the bottom of any docs page to make small changes such as a typo, sentence fix, or a broken link. This takes you to the `.md` file where you can make your changes and [create a pull request](#pull-request) for a review.

#### Make Changes Locally

1. Fork the repository.
2. Install or update to **Node.js**, at the version specified in `.node-version`.
3. Create a working branch and start with your changes!

### Commit Your Update

Commit the changes once you are happy with them. Don't forget to use the "[Self review checklist](https://docs.github.com/en/contributing/collaborating-on-github-docs/self-review-checklist)" to speed up the review process.

### Pull Request

When you're finished with the changes, create a pull request, also known as a PR.

- Fill the "Ready for review" template so that we can review your PR.
- Don't forget to [link PR to issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue) if you are solving one.
- Enable the checkbox to [allow maintainer edits](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/allowing-changes-to-a-pull-request-branch-created-from-a-fork) so the branch can be updated for a merge.

Once you submit your PR, a team member will review your proposal. We may ask questions or request additional information.

- We may ask for changes to be made before a PR can be merged, either using [suggested changes](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/incorporating-feedback-in-your-pull-request) or pull request comments. You can apply suggested changes directly through the UI. You can make any other changes in your fork, then commit them to your branch.
- As you update your PR and apply changes, mark each conversation as [resolved](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/commenting-on-a-pull-request#resolving-conversations).

### Your PR is Merged

Congratulations! Once your PR is merged, your contributions will be publicly visible.

Now that you are part of the community, see how else you can [contribute to the docs](../docs/types-of-contributions.md).

## Windows

This site can be developed on Windows, however a few potential gotchas need to be kept in mind:

1. Regular Expressions: Windows uses `\r\n` for line endings, while Unix-based systems use `\n`. Therefore, when working on Regular Expressions, use `\r?\n` instead of `\n` in order to support both environments.
2. Paths: Windows systems use `\` for the path separator. You could use `path.posix`, `path.posix.join` etc., if you need forward slashes - like for constructing URLs - or ensure your code works with either.
3. Bash: Not every Windows developer has a terminal that fully supports Bash, so it's generally preferred to write scripts in JavaScript instead of Bash.
4. Filename too long error: There is a 260 character limit for a filename when Git is compiled with `msys`. A few workarounds include:
    - Update Git configuration: `git config --system core.longpaths true`
    - Consider using a different Git client on Windows.

## How to Contribute

We need volunteer developers to help this project come to fruition. Here are some important resources:

- [Our roadmap](../docs/roadmap.md) is the 10k foot view of where we're going.
- [Pivotal Tracker](http://pivotaltracker.com/projects/64842) is our day-to-day project management space.
- Mailing list: Join our [developer list](http://groups.google.com/group/opengovernment/)
- Bugs? [Lighthouse](https://participatorypolitics.lighthouseapp.com/projects/47665-opengovernment/overview) is where to report them.

## Testing

We have a handful of tests. Please write tests for new code you create.

## Submitting Changes

Please send a [GitHub Pull Request](https://github.com/opengovernment/opengovernment/pull/new/master) with a clear list of what you've done. When you send a pull request, we will love you forever if you include tests. We can always use more test coverage. Please follow our coding conventions and make sure all of your commits are atomic (one feature per commit).

Always write a clear log message for your commits. One-line messages are fine for small changes, but bigger changes should look like this:

    $ git commit -m "A brief summary of the commit
    > 
    > A paragraph describing what changed and its impact."

## Coding Conventions

Start reading our code and you'll get the hang of it. We optimize for readability:

- We indent using two spaces (soft tabs).
- We avoid logic in views, putting HTML generators into helpers.
- We ALWAYS put spaces after list items and method parameters (`[1, 2, 3]`, not `[1,2,3]`), around operators (`x += 1`, not `x+=1`), and around hash arrows.
- This is open source software. Consider the people who will read your code, and make it look nice for them.

Thanks for contributing!
