# Bookmarks Organizer

![Bookmarks Organizer](/header.png)

Bookmarks Organizer is a powerful Python application that helps you manage, categorize, and maintain your browser bookmarks efficiently. It uses AI-powered categorization to organize your bookmarks intelligently, validates links to keep your collection up-to-date, and provides an easy-to-use interface for managing your digital library.

**Important Note:** This application has only been tested using bookmarks exported from Safari on macOS. It may not work with bookmarks exported from other browsers or operating systems. (For compatibility, see below.)

## Features

- Import bookmarks from standard HTML bookmark files
- Validate bookmark links and remove dead links
- AI-powered categorization (currently using OpenAI's GPT models)
- Customizable protected folders to maintain specific structures
- Export organized bookmarks back to HTML format

## Quick Start Guide

1. **Install Python**: Ensure you have Python 3.8 or newer installed on your system.

2. **Clone the Repository**:
   ```
   git clone https://github.com/rb81/bookmarks-organizer.git
   cd bookmarks-organizer
   ```

3. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Set Up OpenAI API Key**:
   - Create a `.env` file in the project root directory.
   - Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

5. **Prepare Your Bookmarks**:
   - Export your bookmarks from your browser as an HTML file.
   - Name the file `bookmarks.html` and place it in the project root directory.

6. **Run the Application**:
   ```
   python main.py
   ```

## Menu Options

Once you've run the application, select an option from the menu:

```bash
1. Sort all bookmarks
2. Sort uncategorized bookmarks only
```

_**Sort all bookmarks**_ will remove your existing folder structure and recategorize all your bookmarks.

_**Sort uncategorized bookmarks only**_ will look for bookmarks within a folder named `Uncategorized`. This option will retain your existing categories, but may create new ones to accommodate the new bookmarks. This is a useful option. Once your bookmarks are organized, keep a bookmarks folder called `Uncategorized` in your browser and save new bookmarks to it. Once you've collected enough, run the script with this option to categorize these new bookmarks.

If you want to leave bookmarks within specific folders, such as `Favorites` or `Mobile Bookmarks`, simply add these folder names to the `Protected Folders` setting in the `config.yaml` file (as explained further down in this document).

Once completed, a new file called `bookmarks_new.html` will be created in the root folder. Clear out the bookmarks from your browser, and import this new file. You will need to move folders out of the import folder once imported.

If anything goes wrong or if you're unhappy with the resulting categorization, simply delete the bookmarks in your browser, and import the original `bookmarks.html`. (For this reason it's important to retain the original file.)

## Validating and Updating Bookmark Metadata

In all cases, the application will make a request to every URL. Any that are found to be erroneous or unresponsive are removed from your bookmarks and stored in the `data` folder in a file named `retired.json`. By default, bookmarks are only validated and updated if it has been more than 30 days since the last run. To force an update, simply empty out the `data` folder and re-run the script.

## Data Files

The application stores the output of each step in JSON files within the `data` folder. You do not need these files; however, if you retain them, re-running the application will use them to determine whether to validate and update bookmark metadata again.

## Logging

Detailed error logging can be found in the `data` folder. The application creates a log file named `bookmarks_organizer.log` with details on every step of the process.

## Compatibility
 
This application expects your bookmarks to be in the [**Netscape Bookmark File Format**](https://learn.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/platform-apis/aa753582(v=vs.85)), which is the format currently used by Safari in macOS. File format examples provided further down this document.

## Detailed Configuration and Customization

### Configuration File

The `config.yaml` file in the project root directory contains various settings:

```yaml
days_threshold: 30
Protected Folders:
  - "Important"
  - "Work"
max_categories: 20
llm_type: openai
batch_size: 10
```

- `days_threshold`: Number of days before re-validating a bookmark
- `Protected Folders`: List of folders that won't be reorganized
- `max_categories`: Maximum number of categories to create
- `llm_type`: Type of language model to use (currently only 'openai' is supported)
- `batch_size`: Number of bookmarks to process in each batch

### Customizing the Categorization Process

To modify the categorization logic, edit the `openai_llm.py` file. You can adjust the prompt or change the model used for categorization.

### Adding New LLM Providers

To add support for new language model providers:

1. Create a new file (e.g., `new_provider_llm.py`) in the `app` directory.
2. Implement the `LLMInterface` defined in `llm_interface.py`.
3. Update `llm_factory.py` to include the new provider.

## Netscape Bookmark File Format Example

The start of the file should look something like this:

```html
<!DOCTYPE NETSCAPE-Bookmark-file-1>
    <!--This is an automatically generated file.
    It will be read and overwritten.
    Do Not Edit! -->
    <Title>Bookmarks</Title>
    <H1>Bookmarks</H1>
```

The `<DL>` tag wraps the list of items:

```html
<DL>
    {item}
    {item}
    {item}
    .
    .
    .
    </DL>
```

Subfolder should look like this:

```html
<DT><H3 FOLDED ADD_DATE="{date}">{title}</H3>
    <DL><p>
        {item}
        {item}
        {item}
        .
        .
        .
    </DL><p>
```

Bookmarks should look like this:

```html
<DT><A HREF="{url}" ADD_DATE="{date}" LAST_VISIT="{date}" LAST_MODIFIED="{date}">{title}</A>
```

## Project Structure

```
bookmarks-organizer/
│
├── src/
│   ├── __init__.py
│   ├── categorize_bookmarks.py
│   ├── export_bookmarks.py
│   ├── import_bookmarks.py
│   ├── llm_factory.py
│   ├── llm_interface.py
│   ├── log_config.py
│   ├── openai_llm.py
│   ├── reorganize_bookmarks.py
│   └── validate_bookmarks.py
│
├── data/
│   └── (Generated JSON files and log)
│
├── main.py
├── requirements.txt
├── .env
├── config.yaml
└── README.md
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Transparency Disclaimer

[ai.collaboratedwith.me](ai.collaboratedwith.me) in creating this project.