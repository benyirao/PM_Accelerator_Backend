## Project Info

Completed by Yi Rao.

This is the backend assessment project for the PM accelerator internship.

Overview
The Product Manager Accelerator Program is designed to support PM professionals through every stage of their careers. From students looking for entry-level jobs to Directors looking to take on a leadership role, our program has helped over hundreds of students fulfill their career aspirations.

Our Product Manager Accelerator community are ambitious and committed. Through our program they have learnt, honed and developed new PM and leadership skills, giving them a strong foundation for their future endeavors.

Here are the examples of services we offer. Check out our website (link under my profile) to learn more about our services.

🚀 PMA Pro
End-to-end product manager job hunting program that helps you master FAANG-level Product Management skills, conduct unlimited mock interviews, and gain job referrals through our largest alumni network. 25% of our offers came from tier 1 companies and get paid as high as $800K/year. 

🚀 AI PM Bootcamp
Gain hands-on AI Product Management skills by building a real-life AI product with a team of AI Engineers, data scientists, and designers. We will also help you launch your product with real user engagement using our 100,000+ PM community and social media channels. 

🚀 PMA Power Skills
Designed for existing product managers to sharpen their product management skills, leadership skills, and executive presentation skills

🚀 PMA Leader
We help you accelerate your product management career, get promoted to Director and product executive levels, and win in the board room. 

🚀 1:1 Resume Review
We help you rewrite your killer product manager resume to stand out from the crowd, with an interview guarantee.Get started by using our FREE killer PM resume template used by over 14,000 product managers. https://www.drnancyli.com/pmresume

🚀 We also published over 500+ free training and courses. Please go to my YouTube channel https://www.youtube.com/c/drnancyli and Instagram @drnancyli to start learning for free today.

Website
https://www.pmaccelerator.io/
Phone
+19548891063Phone number is +19548891063
Industry
E-Learning Providers
Company size
2-10 employees
181 associated members LinkedIn members who’ve listed Product Manager Accelerator as their current workplace on their profile.
Headquarters
Boston, MA
Founded
2020
Specialties
Product Management, Product Manager, Product Management Training, Product Management Certification, Product Lead, Product Executive, Associate Product Manager, product management coaching, product manager resume, Product Management Interview, VP of Product, Director of Product, Chief Product Officer, and AI Product Management

## Get Started

The backend is developed with Python 3.14.
To run the weather app backend, start a new python environment and install the requirements.

In the terminal of the root directory of this project, run:

`python3 -m venv .venv`
`source .venv/bin/activate`
`python -m pip install -r requirements.txt`

Then, start the local server:

`python -m uvicorn app:app --reload`

## Effort

I developed the backend of this weather app. I implemented the functions so that frontend/user can:
1. Search the latitude and longitude from a city name through Geocoding API.
2. Get the city, state, country, current temperature and weather using latitude and longitude with Geoname and Open-Meteo API together with a Google Map link to that location.
3. Read past requests on current temperature and weather.
4. Update past requested locations with latest temperature and weather.
5. Delete records of past requests on current temperature and weather.
6. Get the city, state, country, and temperature during a time period with user-specified start and end date using Open-Meteo API.
7. Read past requests on temperature within a date range.
8. Update past requested locations with another date period.
9. Delete records of past request on temperature over a period of time.
10. Export both records in JSON format together.
11. Export both records in CSV format separately.
12. Implemented detailed error checking throughout the codebase.