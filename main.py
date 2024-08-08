from flask import Flask, request, render_template, send_file
import pandas as pd
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
import os
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/files'


def get_column_types(df):
    column_types = {}
    for col in df.columns:
        if df[col].dtype == 'object':
            column_types[col] = 'categorical'
        else:
            column_types[col] = 'numerical'
    return column_types


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        method = request.form['method']
        df = pd.read_csv(file)

        # Calculate missing values before cleaning
        before_cleaning = df.isnull().mean().round(4) * 100
        total_missing_percentage = df.isnull().sum().sum() / df.size * 100

        column_types = get_column_types(df)
        numerical_cols = [col for col, col_type in column_types.items() if col_type == 'numerical']
        categorical_cols = [col for col, col_type in column_types.items() if col_type == 'categorical']

        # Choose imputation method based on user selection
        if method == 'mean':
            imputer = SimpleImputer(strategy='mean')
            df[numerical_cols] = imputer.fit_transform(df[numerical_cols])
        elif method == 'median':
            imputer = SimpleImputer(strategy='median')
            df[numerical_cols] = imputer.fit_transform(df[numerical_cols])
        elif method == 'most_frequent':
            imputer = SimpleImputer(strategy='most_frequent')
            df[categorical_cols + numerical_cols] = imputer.fit_transform(df[categorical_cols + numerical_cols])
        elif method == 'knn':
            imputer = KNNImputer(n_neighbors=5)
            df[numerical_cols] = imputer.fit_transform(df[numerical_cols])
        elif method == 'iterative':
            imputer = IterativeImputer()
            df[numerical_cols] = imputer.fit_transform(df[numerical_cols])
        else:
            return "Invalid method"

        # Convert NumPy array back to DataFrame
        cleaned_df = pd.DataFrame(df, columns=df.columns)

        # Save the cleaned DataFrame to a CSV file
        cleaned_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cleaned_dataset.csv')
        cleaned_df.to_csv(cleaned_file_path, index=False)

        # Calculate missing values after cleaning
        after_cleaning = cleaned_df.isnull().mean().round(4) * 100

        # Convert Series to DataFrame
        before_cleaning_df = before_cleaning.reset_index()
        before_cleaning_df.columns = ['Column', 'Percentage']
        after_cleaning_df = after_cleaning.reset_index()
        after_cleaning_df.columns = ['Column', 'Percentage']

        # Generate pie chart for missing values
        pie_chart_path = os.path.join(app.config['UPLOAD_FOLDER'], 'missing_values_pie_chart.png')
        plt.figure(figsize=(8, 6))
        labels = ['Missing', 'Not Missing']
        sizes = [total_missing_percentage, 100 - total_missing_percentage]
        colors = ['#ff9999', '#66b3ff']
        explode = (0.1, 0)  # explode 1st slice
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.title('Total Missing Values Percentage')
        plt.savefig(pie_chart_path)
        plt.close()

        return render_template('results.html',
                               before=before_cleaning_df.to_html(index=False),
                               after=after_cleaning_df.to_html(index=False),
                               data=cleaned_df.to_html(index=False),
                               total_missing_percentage=total_missing_percentage,
                               download_link=cleaned_file_path,
                               pie_chart=pie_chart_path)

    return render_template('index.html')


@app.route('/download')
def download_file():
    path = request.args.get('path')
    return send_file(path, as_attachment=True)


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
