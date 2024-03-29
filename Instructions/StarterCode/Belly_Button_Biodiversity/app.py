import os

import pandas as pd
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Github flagged the following vulnerabilities which were updated on my local machine:
# Jinja2
# #CVE-2019-10906 More information
# high severity
# Vulnerable versions: < 2.10.1
# Patched version: 2.10.1
# In Pallets Jinja before 2.10.1, str.format_map allows a sandbox escape.
#
# SQLAlchemy
# CVE-2019-7164 More information
# moderate severity
# Vulnerable versions: < 1.3.0
# Patched version: 1.3.0
# SQLAlchemy through 1.2.17 and 1.3.x through 1.3.0b2 allows SQL Injection via the order_by parameter.
# and..
# CVE-2019-7548 More information
# moderate severity
# Vulnerable versions: < 1.3.0
# Patched version: 1.3.0
# SQLAlchemy 1.2.17 has SQL Injection when the group_by parameter can be controlled.
# 
# Werkzeug
# CVE-2019-14806 More information
# high severity
# Vulnerable versions: < 0.15.3
# Patched version: 0.15.3
# Pallets Werkzeug before 0.15.3, when used with Docker, has insufficient debugger PIN randomness because Docker containers share the same machine id.

#################################################
# Database Setup
#################################################

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db/bellybutton.sqlite"
db = SQLAlchemy(app)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(db.engine, reflect=True)

# Save references to each table
Samples_Metadata = Base.classes.sample_metadata
Samples = Base.classes.samples


@app.route("/")
def index():
    """Return the homepage."""
    return render_template("index.html")

@app.route("/desert/")
def welcome():
    return"""<html>
    <h1> From Aliens to Bellybuttons? </h1>
    <img src="https://preview.redd.it/btwcedfx9ta31.jpg?auto=webp&s=ef6dce89e836bcd0621d02b756b8180cbfa7c610">
    </html>"""


@app.route("/names")
def names():
    """Return a list of sample names."""

    # Use Pandas to perform the sql query
    stmt = db.session.query(Samples).statement
    df = pd.read_sql_query(stmt, db.session.bind)

    # Return a list of the column names (sample names)
    return jsonify(list(df.columns)[2:])


@app.route("/metadata/<sample>")
def sample_metadata(sample):
    """Return the MetaData for a given sample."""
    sel = [
        Samples_Metadata.sample,
        Samples_Metadata.ETHNICITY,
        Samples_Metadata.GENDER,
        Samples_Metadata.AGE,
        Samples_Metadata.LOCATION,
        Samples_Metadata.BBTYPE,
        Samples_Metadata.WFREQ,
    ]

    results = db.session.query(*sel).filter(Samples_Metadata.sample == sample).all()

    # Create a dictionary entry for each row of metadata information
    sample_metadata = {}
    for result in results:
        sample_metadata["sample"] = result[0]
        sample_metadata["ETHNICITY"] = result[1]
        sample_metadata["GENDER"] = result[2]
        sample_metadata["AGE"] = result[3]
        sample_metadata["LOCATION"] = result[4]
        sample_metadata["BBTYPE"] = result[5]
        sample_metadata["WFREQ"] = result[6]

    print(sample_metadata)
    return jsonify(sample_metadata)


@app.route("/samples/<sample>")
def samples(sample):
    """Return `otu_ids`, `otu_labels`,and `sampled_values`."""
    stmt = db.session.query(Samples).statement
    df = pd.read_sql_query(stmt, db.session.bind)

    # Filter the data based on the sample number and
    # only keep rows with values above 1
    sample_data = df.loc[df[sample] > 1, ["otu_id", "otu_label", sample]]
    # Format the data to send as json
    data = {
        "otu_ids": sample_data.otu_id.values.tolist(),
        "sampled_values": sample_data[sample].values.tolist(),
        "otu_labels": sample_data.otu_label.tolist(),
    }
    return jsonify(data)


if __name__ == "__main__":
    app.run()
