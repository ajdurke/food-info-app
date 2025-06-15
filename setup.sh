mkdir -p app/config/google_sheets/database \
         app/config/google_sheets/helpers \
         app/config/google_sheets/ui/templates

touch app/config/google_sheets/google_sheets_connector.py

touch app/config/google_sheets/helpers/utils.py \
      app/config/google_sheets/helpers/nutrition.py \
      app/config/google_sheets/helpers/environment.py \
      app/config/google_sheets/helpers/cost.py \
      app/config/google_sheets/helpers/filters.py \
      app/config/google_sheets/helpers/recipe.py \
      app/config/google_sheets/helpers/user.py

touch app/config/google_sheets/ui/streamlit_app.py \
      app/config/google_sheets/ui/templates/base.html \
      app/config/google_sheets/ui/templates/index.html \
      app/config/google_sheets/ui/templates/meal_details.html \
      app/config/google_sheets/ui/templates/modify_recipe.html \
      app/config/google_sheets/ui/templates/cook_log.html \
      app/config/google_sheets/ui/templates/stats.html