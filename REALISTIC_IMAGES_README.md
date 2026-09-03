# Curex realistic diagnostic test images

This version replaces the generic category icons in the product catalog with product-specific JPG files stored in:

`media/products/real_tests/`

Every product record in `db.sqlite3` now points to its own image file. The catalog template was also updated to display the images larger and more prominently.

After extracting the project:

```powershell
python manage.py migrate
python manage.py runserver
```

Then refresh the catalog with Ctrl+F5.
