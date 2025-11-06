from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
import csv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import ai
import automation
import random
from datetime import datetime


app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)
# Load environment variables
load_dotenv()

campaign_lead_list_association = db.Table('campaign_lead_list_association',
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'), primary_key=True),
    db.Column('lead_list_id', db.Integer, db.ForeignKey('lead_list.id'), primary_key=True)
)
class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(200), nullable=True)
    state = db.Column(db.String(200), nullable=True)
    country = db.Column(db.String(200), nullable=True)
    zip = db.Column(db.String(200), nullable=True)

    # Relationship to Property
    properties = db.relationship('Property', backref='lead', lazy=True)
    lead_list_id = db.Column(db.Integer, db.ForeignKey('lead_list.id'), nullable=True)
    campaignid = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True)

    last_modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Lead {self.firstname} {self.lastname}>'

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(100), nullable=False, default="notstarted")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to Lead
    leads = db.relationship('Lead', backref='campaign', lazy=True)
    lead_lists = db.relationship('LeadList', secondary=campaign_lead_list_association, back_populates='campaigns')

    def __repr__(self):
        return f'<Campaign {self.name}>'

class LeadList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to Lead
    leads = db.relationship('Lead', backref='lead_list', lazy=True)

    campaigns = db.relationship('Campaign', secondary=campaign_lead_list_association, back_populates='lead_lists')

    def __repr__(self):
        return f'<LeadList {self.name}>'
# Define Property model
class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.Float, nullable=True)
    beds = db.Column(db.Integer, nullable=True)
    baths = db.Column(db.Integer, nullable=True)
    type = db.Column(db.String(50), nullable=True)
    livingarea = db.Column(db.Float, nullable=True)
    features = db.Column(db.String(200), nullable=True)
    propertyaddress = db.Column(db.String(200), nullable=True)
    yearsbuilt = db.Column(db.Integer, nullable=True)
    occupancy = db.Column(db.String(50), nullable=True)

    # Foreign key to Lead
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)

    def __repr__(self):
        return f'<Property {self.propertyaddress} of Lead ID {self.lead_id}>'

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    phone_number = db.Column(db.String(15), nullable=False)  # Phone number
    message = db.Column(db.Text, nullable=False)  # Chat message
    direction = db.Column(db.String(10), nullable=False)  # 'incoming' or 'outgoing'

    def __repr__(self):
        return f'<ChatHistory {self.phone_number} - {self.direction}>'


@app.route("/", methods=["POST", "GET"])
def index():
    all_leads = Lead.query.all()
    lead_lists = LeadList.query.all()

    return render_template("all_leads.html", leads=all_leads, lead_lists=lead_lists)



@app.route("/leads", methods=["POST", "GET"])
def leads():
    # Query all leads and their related properties
    all_leads = Lead.query.all()
    lead_lists = LeadList.query.all()

    return render_template("all_leads.html", leads=all_leads, lead_lists=lead_lists)

@app.route("/lead/<int:lead_id>", methods=["GET"])
def leaddetails(lead_id):
    # Query the lead by ID
    lead = Lead.query.get_or_404(lead_id)
    return render_template("singlelead.html", lead=lead)

@app.route("/leads/edit/<int:lead_id>", methods=["GET", "POST"])
def edit_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)

    # Assuming a lead can have only one property for this example
    property_info = lead.properties[0] if lead.properties else None

    if request.method == "POST":
        lead.firstname = request.form["firstname"]
        lead.lastname = request.form["lastname"]
        lead.phone = request.form["phone"]
        lead.email = request.form["email"]
        lead.status = request.form["status"]
        lead.address = request.form["address"]
        lead.city = request.form["city"]
        lead.state = request.form["state"]
        lead.country = request.form["country"]
        lead.zip = request.form["zip"]

        # Update property information if it exists
        if property_info:
            property_info.size = request.form["size"]
            property_info.beds = request.form["beds"]
            property_info.baths = request.form["baths"]
            property_info.type = request.form["type"]
            property_info.livingarea = request.form["livingarea"]
            property_info.features = request.form["features"]
            property_info.propertyaddress = request.form["propertyaddress"]
            property_info.yearsbuilt = request.form["yearsbuilt"]
            property_info.occupancy = request.form["occupancy"]
        else:
            # Create new property if none exists (optional)
            new_property = Property(
                size=request.form["size"],
                beds=request.form["beds"],
                baths=request.form["baths"],
                type=request.form["type"],
                livingarea=request.form["livingarea"],
                features=request.form["features"],
                propertyaddress=request.form["propertyaddress"],
                yearsbuilt=request.form["yearsbuilt"],
                occupancy=request.form["occupancy"],
                lead=lead  # Associate the new property with the lead
            )
            db.session.add(new_property)

        db.session.commit()
        return redirect(url_for("leads"))

    return render_template("edit_lead.html", lead=lead, property_info=property_info)


@app.route("/leads/delete/<int:lead_id>", methods=["POST"])
def delete_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)

    # Manually delete associated properties
    for property in lead.properties:
        db.session.delete(property)

    db.session.delete(lead)
    db.session.commit()

    flash('Lead and associated properties deleted successfully!')
    return redirect(url_for("leads"))


@app.route("/incomingleads", methods=["POST"])
def incomingleads():
    if request.method == "POST":
        data = request.get_json()

        # Extract Lead information
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        phone = data.get("phone")
        email = data.get("email")
        status = data.get("status")
        address = data.get("address")
        city = data.get("city")
        state = data.get("state")
        country = data.get("country")
        zip_code = data.get("zip")
        propertyinfo = data.get("propertyinfo")  # Expecting a list of properties

        # Validate Lead data
        if not all([firstname, lastname, phone, email, status]):
            return jsonify({"error": "Missing required lead fields"}), 400

        # Create Lead instance
        new_lead = Lead(
            firstname=firstname,
            lastname=lastname,
            phone=phone,
            email=email,
            status="initial",
            address=address,
            city=city,
            state=state,
            country=country,
            zip=zip_code
        )
        db.session.add(new_lead)

        # Validate and add Property information if provided
        if propertyinfo:
            for prop in propertyinfo:
                size = prop.get("size")
                beds = prop.get("beds")
                baths = prop.get("baths")
                type = prop.get("type")
                livingarea = prop.get("livingarea")
                features = prop.get("features")
                propertyaddress = prop.get("propertyaddress")
                yearsbuilt = prop.get("yearsbuilt")
                occupancy = prop.get("occupancy")

                # Ensure at least one identifying field for Property is present
                if not propertyaddress:
                    continue  # Skip this property if the address is missing

                # Create Property instance and associate it with the lead
                new_property = Property(
                    size=size,
                    beds=beds,
                    baths=baths,
                    type=type,
                    livingarea=livingarea,
                    features=features,
                    propertyaddress=propertyaddress,
                    yearsbuilt=yearsbuilt,
                    occupancy=occupancy,
                    lead=new_lead  # Associate property with the lead
                )
                db.session.add(new_property)

        # Commit all changes to the database
        db.session.commit()

        return jsonify({"message": "Lead and associated properties added successfully"}), 201


@app.route("/add", methods=["GET", "POST"])
def add_lead():
    if request.method == "POST":
        # Create new Lead object
        new_lead = Lead(
            firstname=request.form["firstname"],
            lastname=request.form["lastname"],
            phone=request.form["phone"],
            email=request.form["email"],
            status=request.form["status"],
            address=request.form["address"],
            city=request.form["city"],
            state=request.form["state"],
            country=request.form["country"],
            zip=request.form["zip"]
        )

        # Create new Property object
        new_property = Property(
            size=request.form["size"],
            beds=request.form["beds"],
            baths=request.form["baths"],
            type=request.form["type"],
            livingarea=request.form["livingarea"],
            features=request.form["features"],
            propertyaddress=request.form["propertyaddress"],
            yearsbuilt=request.form["yearsbuilt"],
            occupancy=request.form["occupancy"],
            lead=new_lead  # Associate the property with the lead
        )

        # Add to the session
        db.session.add(new_lead)
        db.session.add(new_property)
        db.session.commit()

        return redirect(url_for("leads"))

    return render_template("add_lead.html")



@app.route("/upload", methods=["GET", "POST"])
def import_leads():
    all_leads = Lead.query.all()
    if request.method == "POST":
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            csv_file = csv.reader(file.stream.read().decode("UTF-8").splitlines())
            next(csv_file)  # Skip header row

            for row in csv_file:
                # Ensure the CSV has enough columns
                if len(row) < 19:
                    flash(f'Not enough columns in the row: {row}')
                    continue

                try:
                    # Extract and map data from the row with default handling
                    firstname = row[0] or "Unknown"
                    lastname = row[1] or "Unknown"
                    phone = f"+1 {row[2]}" if row[2] else "+1 N/A"
                    email = row[3] or "N/A"
                    status = "initial"
                    address = row[5] or "N/A"
                    city = row[6] or "N/A"
                    state = row[7] or "N/A"
                    country = row[8] or "United States"
                    zip_code = row[9] or "N/A"

                    size = float(row[10]) if row[10] else 0.0
                    beds = int(row[11]) if row[11] else 0
                    baths = int(row[12]) if row[12] else 0
                    property_type = row[13] or "Unknown"
                    living_area = float(row[14]) if row[14] else 0.0
                    features = row[15] or "None"
                    property_address = row[16] or "N/A"
                    year_built = int(row[17]) if row[17] else 2000
                    occupancy = row[18] or "Unknown"

                    # Create new Lead object
                    new_lead = Lead(
                        firstname=firstname,
                        lastname=lastname,
                        phone=phone,
                        email=email,
                        status=status,
                        address=address,
                        city=city,
                        state=state,
                        country=country,
                        zip=zip_code
                    )

                    # Create new Property object
                    new_property = Property(
                        size=size,
                        beds=beds,
                        baths=baths,
                        type=property_type,
                        livingarea=living_area,
                        features=features,
                        propertyaddress=property_address,
                        yearsbuilt=year_built,
                        occupancy=occupancy,
                        lead=new_lead  # Associate property with the lead
                    )

                    # Add both objects to the session
                    db.session.add(new_lead)
                    db.session.add(new_property)

                except Exception as e:
                    flash(f'Error processing row: {row}. Error: {str(e)}')
                    continue  # Skip this row and proceed to the next

            db.session.commit()
            flash('Leads imported successfully!')
            return redirect(url_for("leads"))

    return render_template("upload.html", leads=all_leads)
@app.route("/lead-lists/add", methods=["GET", "POST"])
def create_lead_list():
    if request.method == "POST":
        # Get lead list name and description
        name = request.form.get("name")
        description = request.form.get("description")

        # Validate the input
        if not name:
            flash("Lead List name is required", "error")
            return redirect(url_for("create_lead_list"))

        # Create and save the new lead list
        lead_list = LeadList(name=name, description=description)
        db.session.add(lead_list)
        db.session.commit()  # Commit to generate the lead_list.id

        # Add selected leads to the lead list
        selected_lead_ids = request.form.getlist('selected_leads')
        for lead_id in map(int, selected_lead_ids):  # Convert IDs to integers
            lead = Lead.query.get(lead_id)
            if lead:
                lead.lead_list_id = lead_list.id
                db.session.add(lead)

        # Commit changes to assign leads
        db.session.commit()
        flash("Lead List created successfully with selected leads!", "success")
        return redirect(url_for("view_lead_lists"))

    # Retrieve all leads for the template
    return render_template("createnewleadlist.html")



@app.route("/lead-lists/addcsv", methods=["GET", "POST"])
def create_lead_listbulk():
    if request.method == "POST":
        # Get lead list name and description
        name = request.form.get("name")
        description = request.form.get("description")

        # Validate the input
        if not name:
            flash("Lead List name is required", "error")
            return redirect(url_for("create_lead_list"))

        # Create and save new Lead List
        lead_list = LeadList(name=name, description=description)
        db.session.add(lead_list)
        db.session.commit()

        # Handle manually selected leads
        selected_lead_ids = request.form.getlist('selected_leads')
        print(selected_lead_ids)
        for lead_id in selected_lead_ids:
            lead = Lead.query.get(lead_id)
            if lead:
                lead.lead_list_id = lead_list.id
                db.session.add(lead)

        # Handle CSV file upload if provided
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            try:
                csv_file = csv.reader(file.stream.read().decode("UTF-8").splitlines())
                next(csv_file)  # Skip header row

                for row in csv_file:
                    if len(row) < 19:
                        flash(f'Row has insufficient columns: {row}', 'warning')
                        continue

                    firstname = row[0] or "Unknown"
                    lastname = row[1] or "Unknown"
                    phone = f"+1 {row[2]}" if row[2] else "+1 N/A"
                    email = row[3] or "N/A"
                    status = "initial"
                    address = row[5] or "N/A"
                    city = row[6] or "N/A"
                    state = row[7] or "N/A"
                    country = row[8] or "United States"
                    zip_code = row[9] or "N/A"

                    size = float(row[10]) if row[10] else 0.0
                    beds = int(row[11]) if row[11] else 0
                    baths = int(row[12]) if row[12] else 0
                    property_type = row[13] or "Unknown"
                    living_area = float(row[14]) if row[14] else 0.0
                    features = row[15] or "None"
                    property_address = row[16] or "N/A"
                    year_built = int(row[17]) if row[17] else 2000
                    occupancy = row[18] or "Unknown"

                    # Create Lead and Property objects
                    new_lead = Lead(
                        firstname=firstname,
                        lastname=lastname,
                        phone=phone,
                        email=email,
                        status=status,
                        address=address,
                        city=city,
                        state=state,
                        country=country,
                        zip=zip_code,
                        lead_list_id=lead_list.id
                    )

                    new_property = Property(
                        size=size,
                        beds=beds,
                        baths=baths,
                        type=property_type,
                        livingarea=living_area,
                        features=features,
                        propertyaddress=property_address,
                        yearsbuilt=year_built,
                        occupancy=occupancy,
                        lead=new_lead  # Associate property with the lead
                    )

                    db.session.add(new_lead)
                    db.session.add(new_property)

            except Exception as e:
                flash(f"Error processing CSV file: {str(e)}", "error")
                return redirect(url_for("create_lead_list"))

        db.session.commit()
        flash("Lead List and associated leads created successfully!", "success")
        return redirect(url_for("view_lead_lists"))

    # Pass all leads to the template for selection
    leads = Lead.query.all()
    return render_template("create_lead_list.html", leads=leads)





@app.route("/lead-lists/edit/<int:lead_list_id>", methods=["GET", "POST"])
def edit_lead_list(lead_list_id):
    lead_list = LeadList.query.get_or_404(lead_list_id)

    if request.method == "POST":
        lead_list.name = request.form.get("name")
        lead_list.description = request.form.get("description")

        db.session.commit()
        flash("Lead List updated successfully!", "success")
        return redirect(url_for("view_lead_lists"))

    return render_template("edit_lead_list.html", lead_list=lead_list)


@app.route("/lead-lists/delete/<int:lead_list_id>", methods=["POST","GET"])
def delete_lead_list(lead_list_id):
    lead_list = LeadList.query.get_or_404(lead_list_id)

    # Delete associated leads before deleting the lead list
    for lead in lead_list.leads:
        db.session.delete(lead)

    db.session.delete(lead_list)
    db.session.commit()

    flash("Lead List and all associated leads deleted successfully!", "success")
    return redirect(url_for("view_lead_lists"))

@app.route("/leadlist/<int:lead_list_id>/remove-lead/<int:lead_id>", methods=["POST"])
def remove_lead_from_list(lead_list_id, lead_id):
    # Retrieve the lead
    lead = Lead.query.filter_by(id=lead_id, lead_list_id=lead_list_id).first_or_404()

    # Remove the lead from the lead list
    lead.lead_list_id = None
    db.session.commit()

    flash("Lead removed from the lead list successfully.", "success")
    return redirect(url_for("view_lead_list", lead_list_id=lead_list_id))

@app.route("/lead-lists",methods=["POST","GET"])
def view_lead_lists():
    lead_lists = LeadList.query.all()  #

    return render_template("lead_list.html", lead_lists=lead_lists)

@app.route("/leadlist/leads/<int:lead_list_id>", methods=["GET"])
def view_lead_list(lead_list_id):
    # Retrieve the specific lead list by ID
    lead_list = LeadList.query.get_or_404(lead_list_id)
    # Retrieve all leads associated with this lead list
    leads = Lead.query.filter_by(lead_list_id=lead_list.id).all()

    return render_template("viewlist.html", lead_list=lead_list, leads=leads)

@app.route("/search-lead-lists", methods=["GET"])
def search_lead_lists():
    # AJAX endpoint to search lead lists
    query = request.args.get("query", "")
    leads = LeadList.query.filter(LeadList.name.ilike(f"%{query}%")).all()
    lead_list_data = [{"id": ll.id, "name": ll.name} for ll in leads]
    return jsonify(lead_list_data)



@app.route("/search-lead", methods=["GET"])
def search_lead():
    # AJAX endpoint to search lead lists
    query = request.args.get("query", "")
    leads = Lead.query.filter(Lead.firstname.ilike(f"%{query}%") | Lead.lastname.ilike(f"%{query}%")).all()
    lead_data = [{"id": lead.id, "name": f"{lead.firstname} {lead.lastname}"} for lead in leads]
    return jsonify(lead_data)

@app.route("/campaign", methods=["GET"])
def campaignlist():
    # List all campaigns with lead lists eagerly loaded
    campaigns = Campaign.query.options(db.joinedload(Campaign.lead_lists)).all()
    return render_template("all_campaign.html", campaigns=campaigns)

@app.route("/campaign/add", methods=["GET", "POST"])
def add_campaign():
    if request.method == "POST":
        # Get campaign name from form
        name = request.form.get("name")

        # Validate campaign name
        if not name:
            flash("Campaign name is required", "error")
            return redirect(url_for("add_campaign"))

        # Create and save new campaign
        campaign = Campaign(name=name)
        db.session.add(campaign)
        db.session.flush()  # Flush to get the campaign ID before associating lead lists

        # Add selected lead lists to the campaign
        lead_list_ids = request.form.getlist("lead_list_ids")
        for lead_list_id in lead_list_ids:
            lead_list = LeadList.query.get(lead_list_id)
            if lead_list:
                campaign.lead_lists.append(lead_list)  # Use append to set the many-to-many relationship

        db.session.commit()

        flash("Campaign created successfully with selected lead lists!", "success")
        return redirect(url_for("campaignlist"))

    return render_template("add_camp.html")


@app.route("/campaign/delete/<int:campaign_id>", methods=["POST"])
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash("Campaign deleted successfully!", "success")
    return redirect(url_for("campaignlist"))


@app.route("/campaign/edit/<int:campaign_id>", methods=["GET", "POST"])
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")

        # Update campaign details
        campaign.name = name
        campaign.description = description
        db.session.commit()

        flash("Campaign updated successfully!", "success")
        return redirect(url_for("campaignlist"))

    return render_template("edit_campaign.html", campaign=campaign)


@app.route("/campaign/view/<int:campaign_id>", methods=["GET"])
def view_campaign(campaign_id):
    campaign = Campaign.query.options(db.joinedload(Campaign.lead_lists)).get_or_404(campaign_id)
    return render_template("campignview.html", campaign=campaign)


# Main entry point



@app.route('/assign-leads-to-list', methods=['POST'])
def assign_leads_to_list():
    data = request.get_json()
    lead_ids = data.get('lead_ids', [])
    lead_list_id = data.get('lead_list_id')
    new_list_name = data.get('new_list_name')

    if not lead_ids:
        return jsonify({'error': 'No leads selected'}), 400

    # If a new list is being created
    if new_list_name:
        lead_list = LeadList(name=new_list_name)
        db.session.add(lead_list)
        db.session.flush()  # Get the new lead list ID
    else:
        # Get the existing lead list
        lead_list = LeadList.query.get(lead_list_id)
        if not lead_list:
            return jsonify({'error': 'Invalid lead list'}), 400

    # Assign leads to the lead list
    leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
    for lead in leads:
        lead.lead_list = lead_list

    db.session.commit()
    return jsonify({'message': 'Leads assigned successfully'}), 200


def get_chat_history(phone_number):
    return ChatHistory.query.filter_by(phone_number=phone_number).order_by(ChatHistory.id).all()


@app.route('/incomingsms', methods=['GET', 'POST'])
def incomingsms():
    incoming_data = request.values  # Use 'args' for GET requests
    print(incoming_data)
    from_number = incoming_data.get('From')
    message_body = incoming_data.get('Body')

    # Save the incoming message as "user" in the chat history
    chat = ChatHistory(phone_number=from_number, message=message_body, direction='incoming')
    db.session.add(chat)
    db.session.commit()

    # Fetch previous chat history for the phone number
    history = get_chat_history(from_number)
    conversation_history = []
    response = ''
    lead = Lead.query.filter_by(phone=from_number).first()
    if lead:
        name = lead.firstname
        phone = lead.phone
        address = lead.properties[0].propertyaddress if lead.properties[0].propertyaddress else lead.address
        # Ensure the lead exists
        if lead.lead_list:  # Check if the lead belongs to any lead list
            campaigns = lead.lead_list.campaigns  # Access campaigns through the lead's lead list
            if campaigns:
                print("Campaigns associated with the lead:")
                for campaign in campaigns:
                    print(f"- {campaign.name}")
                    if campaign.status == "running":
                        sentiment = ai.getsentiemnt(message_body)  # Analyze the sentiment of the message body
                        if sentiment == "stop":
                            lead.status = "unsubscribed"  # Update the status of the lead
                            db.session.commit()
                            response = "unsubscribed"
                        else:
                            for message in history:
                                if message.direction == 'incoming':
                                    conversation_history.append({"role": "user", "content": message.message})
                                elif message.direction == 'outgoing':
                                    conversation_history.append({"role": "assistant", "content": message.message})

                                # Add the latest user message
                            conversation_history.append({"role": "user", "content": message_body})
                            formeeting = ai.calendly(conversation_history)
                            # Generate the AI's response using the conversation history

                            if formeeting == "nomeeting":
                                reply = ai.conversation(conversation_history, name, phone, address)
                                print(reply)
                                messagesend = automation.sendsms(phone,reply)
                                print(messagesend)

                                # Save the outgoing message as "assistant" in the chat history
                                reply_chat = ChatHistory(phone_number=from_number, message=reply, direction='outgoing')
                                db.session.add(reply_chat)
                                lead.status = "ongoing"
                                db.session.commit()
                            else:
                                print(formeeting)
                                reply = ai.conversation(conversation_history, name, phone, address)
                                messagesend = automation.sendsms(phone,reply)
                                print(messagesend)
                                if lead.status == "meetingarranged":
                                    reply_chat = ChatHistory(phone_number=from_number, message=reply,
                                                             direction='outgoing')
                                    db.session.add(reply_chat)
                                else:


                                    reply_chat = ChatHistory(phone_number=from_number, message=reply,
                                                             direction='outgoing')
                                    db.session.add(reply_chat)

                                    lead.status = "meetingarranged"
                                    db.session.commit()

                                lead.status = "meetingarranged"
                                db.session.commit()
                    else:
                        print("leads with following campaign stopped")
            else:
                print("No campaigns associated with this lead's lead list.")
        else:
            print("This lead is not part of any lead list.")

    else:
        print(f"No lead found with phone number: {from_number}")



    # Send the AI response as a reply to the incoming SMS (optional)
    return jsonify({"reply": response})

@app.route("/stopcampaign/<int:campaign_id>", methods=["POST", "GET"])
def stopcampaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.status = "stopped"
    db.session.commit()
    return redirect(url_for("campaignlist"))

@app.route("/startcampaign/<int:campaign_id>", methods=["POST", "GET"])
def startcampaign(campaign_id):
    # Get the campaign by ID
    campaign = Campaign.query.get_or_404(campaign_id)

    # Search for leads associated with this campaign
    indirect_leads = Lead.query.filter(Lead.lead_list_id.in_([lead_list.id for lead_list in campaign.lead_lists])
    ).all()

    campaign.status = "running"
    db.session.commit()

    # Debugging: Print the leads found
    print(f"Starting campaign {campaign.name}. Leads found: {[lead.firstname for lead in indirect_leads]}")

    # Perform any specific campaign start logic here

    for lead in indirect_leads:
        name = lead.firstname
        phone = lead.phone
        address = lead.properties[0].propertyaddress if lead.properties[0].propertyaddress else lead.address
        if lead.status == "initial":
            try:
                sendfirstsms = automation.firstagent(name,address,phone)
                print(sendfirstsms)

            except:
                pass
            lead.status = "sendsms"
            db.session.commit()
        elif lead.status == "unsubscribed":
            print("lead unsubscribed")
        else:
            try:
                sendfirstsms = automation.firstagent(name,address,phone)
                print(sendfirstsms)
            except:
                pass
            lead.status = "sentsms"
            db.session.commit()


    if not indirect_leads:
        flash(f"No leads found for campaign '{campaign.name}'", "warning")
        return redirect(url_for("campaignlist"))

    # Example: Mark campaign as started


    flash(f"Campaign '{campaign.name}' has started successfully!", "success")
    return redirect(url_for("campaignlist"))

@app.route("/analytics", methods=["GET", "POST"])
def analytics():
    # Extract campaign ID and date filters from the request parameters
    campaign_id = request.args.get("campaign_id", type=int)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Base query
    query = Lead.query

    # Apply campaign filter if provided
    if campaign_id:
        campaign = Campaign.query.get_or_404(campaign_id)
        lead_list_ids = [lead_list.id for lead_list in campaign.lead_lists]
        query = query.filter(Lead.lead_list_id.in_(lead_list_ids))

    # Apply date range filter if provided
    if start_date:
        query = query.filter(Lead.last_modified >= start_date)
    if end_date:
        query = query.filter(Lead.last_modified <= end_date)

    # Totals for analytics metrics
    total_sent = query.filter_by(status="sendsms").count()
    total_responded = query.filter_by(status="ongoing").count()
    total_converted = query.filter_by(status="meetingarranged").count()
    total_do_not_call = query.filter_by(status="unsubscribed").count()

    # Calculate rates
    response_rate = round((total_responded / total_sent * 100), 2) if total_sent > 0 else 0
    conversion_rate = round((total_converted / total_sent * 100), 2) if total_sent > 0 else 0

    # Day-wise data for the chart
    day_wise_data = query.with_entities(
        func.date(Lead.last_modified).label("date"),
        func.count().label("count")
    ).group_by(func.date(Lead.last_modified)).order_by(func.date(Lead.last_modified)).all()

    # Format day-wise data for the frontend
    formatted_day_wise_data = [{"date": str(row.date), "count": row.count} for row in day_wise_data]

    # Fetch all campaigns for the dropdown
    campaigns = Campaign.query.all()

    # Render the template with filtered data
    return render_template(
        "analytics.html",
        total_sent=total_sent,
        response_rate=response_rate,
        conversion_rate=conversion_rate,
        total_do_not_call=total_do_not_call,
        day_wise_data=formatted_day_wise_data,
        campaigns=campaigns,
        selected_campaign=campaign_id,
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)