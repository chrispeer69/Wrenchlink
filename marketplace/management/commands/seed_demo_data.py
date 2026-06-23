from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from marketplace.models import (
    Application,
    ApplicationMessage,
    Certification,
    CityPool,
    CredentialAccessRequest,
    Education,
    EmployerProfile,
    EmployerReview,
    Job,
    Notification,
    NotificationPreference,
    ProfessionalReference,
    SavedJob,
    TechnicianProfile,
    TechnicianReview,
    WorkHistory,
)


DEMO_PASSWORD = "WrenchLinkDemo!2026"


class Command(BaseCommand):
    help = "Create idempotent WrenchLink demo data for local or staging use."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "Refusing to seed while DJANGO_DEBUG=False. "
                "Demo data is for local or staging environments only."
            )
        pools = self.create_pools()
        employers = self.create_employers(pools)
        technicians = self.create_technicians(pools)
        jobs = self.create_jobs(pools, employers)
        self.create_profiles(technicians)
        self.create_activity(technicians, jobs, employers)
        self.stdout.write(self.style.SUCCESS("WrenchLink demo data is ready."))
        self.stdout.write(f"Technician: marcus@demo.wrenchlink.io / {DEMO_PASSWORD}")
        self.stdout.write(f"Employer: hiring@apex.demo.io / {DEMO_PASSWORD}")
        self.stdout.write("Existing superusers were not changed.")

    def create_pools(self):
        rows = [
            ("Columbus", "Ohio", "OH", "Midwest"),
            ("Cleveland", "Ohio", "OH", "Midwest"),
            ("Atlanta", "Georgia", "GA", "Southeast"),
            ("Dallas", "Texas", "TX", "Southwest"),
            ("Chicago", "Illinois", "IL", "Midwest"),
            ("Phoenix", "Arizona", "AZ", "Southwest"),
            ("Houston", "Texas", "TX", "Southwest"),
            ("Charlotte", "North Carolina", "NC", "Southeast"),
            ("Detroit", "Michigan", "MI", "Midwest"),
            ("Tampa", "Florida", "FL", "Southeast"),
            ("Denver", "Colorado", "CO", "West"),
            ("Boston", "Massachusetts", "MA", "Northeast"),
        ]
        pools = {}
        for name, state, code, region in rows:
            pool, _ = CityPool.objects.update_or_create(
                name=name,
                state_code=code,
                defaults={"state": state, "region": region, "is_active": True},
            )
            pools[name] = pool
        return pools

    def create_user(self, email, first, last, role):
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                "email": email,
                "first_name": first,
                "last_name": last,
                "role": role,
                "email_verified": True,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user

    def create_employers(self, pools):
        rows = [
            ("Apex Body & Auto", "hiring@apex.demo.io", "Apex", "Hiring", "collision", "Columbus", "Independent repair and collision center focused on modern diagnostics.", ["ASE training", "Climate-controlled shop", "Tool allowance", "Paid time off"]),
            ("Summit Collision Center", "jobs@summit.demo.io", "Summit", "Hiring", "collision", "Columbus", "I-CAR focused collision center with modern frame equipment.", ["I-CAR training", "Health insurance", "Modern equipment"]),
            ("Precision Motors", "careers@precision.demo.io", "Precision", "Hiring", "repair", "Columbus", "Advanced diagnostics and EV/hybrid repair facility.", ["Manufacturer training", "EV safety training", "401k"]),
            ("FastLane Service", "team@fastlane.demo.io", "FastLane", "Hiring", "repair", "Columbus", "High-volume service center with paid apprenticeships.", ["Paid training", "ASE testing support", "Flexible schedules"]),
            ("Cleveland Auto Group", "jobs@clevelandauto.demo.io", "Cleveland", "Hiring", "dealer", "Cleveland", "Dealer service group with OEM training pathways.", ["OEM training", "Flat-rate guarantee", "Health insurance"]),
            ("GearHead Transmissions", "jobs@gearhead.demo.io", "GearHead", "Hiring", "repair", "Atlanta", "Transmission diagnostics, R&R and rebuilding specialists.", ["Commission upside", "Steady volume", "Tool allowance"]),
            ("Dallas Drive Auto", "careers@dallasdrive.demo.io", "Dallas", "Hiring", "repair", "Dallas", "Full-service shop with a structured apprenticeship program.", ["Mentorship", "ASE tuition assistance", "Weekly pay"]),
        ]
        employers = {}
        for company, email, first, last, shop_type, metro, description, perks in rows:
            user = self.create_user(email, first, last, User.Role.EMPLOYER)
            profile, _ = EmployerProfile.objects.update_or_create(
                user=user,
                defaults={
                    "company_name": company,
                    "shop_type": shop_type,
                    "city_pool": pools[metro],
                    "description": description,
                    "phone": "(555) 010-2026",
                    "perks": perks,
                    "verification_status": EmployerProfile.VerificationStatus.VERIFIED,
                    "is_verified": True,
                    "rejection_reason": "",
                },
            )
            employers[company] = profile
        return employers

    def create_technicians(self, pools):
        rows = [
            ("Marcus", "Thompson", "marcus@demo.wrenchlink.io", "Master Technician", 9, "Columbus", ["ASE Master", "EV/Hybrid", "Diagnostics"]),
            ("Jordan", "Rivera", "jordan@demo.wrenchlink.io", "Collision / Body Technician", 7, "Columbus", ["I-CAR Gold", "Frame Work", "Paint Matching"]),
            ("Darnell", "Adams", "darnell@demo.wrenchlink.io", "EV Specialist", 5, "Columbus", ["ASE L3 EV", "ADAS", "High Voltage"]),
            ("Sofia", "Nguyen", "sofia@demo.wrenchlink.io", "Paint Technician", 6, "Columbus", ["Waterborne", "Color Match", "Downdraft"]),
            ("Tyler", "Brooks", "tyler@demo.wrenchlink.io", "General Service Technician", 3, "Cleveland", ["ASE G1", "Brakes", "Suspension"]),
            ("Maria", "Castillo", "maria@demo.wrenchlink.io", "Collision Estimator", 8, "Cleveland", ["I-CAR Platinum", "CCC One", "Supplements"]),
            ("Andre", "Wallace", "andre@demo.wrenchlink.io", "Transmission Specialist", 12, "Atlanta", ["ASE A2", "CVT", "Rebuild"]),
            ("Priya", "Patel", "priya@demo.wrenchlink.io", "Diesel / Fleet Technician", 6, "Dallas", ["ASE T-Series", "DPF", "Hydraulics"]),
        ]
        technicians = {}
        for first, last, email, title, years, metro, skills in rows:
            user = self.create_user(email, first, last, User.Role.TECHNICIAN)
            profile, _ = TechnicianProfile.objects.update_or_create(
                user=user,
                defaults={
                    "city_pool": pools[metro],
                    "professional_title": title,
                    "bio": f"{title} with {years} years of hands-on automotive experience.",
                    "phone": "(555) 019-2026",
                    "years_experience": years,
                    "availability": "active",
                    "preferred_schedule": "Full-Time",
                    "skills": skills,
                    "is_visible": True,
                },
            )
            technicians[email] = profile
        return technicians

    def create_jobs(self, pools, employers):
        rows = [
            ("Master Technician — Diagnostics", "Apex Body & Auto", "Columbus", "repair", 75, 95, 8, "ASE Required", "Lead diagnostic technician for drivability, electrical and ADAS calibration."),
            ("Auto Body Repair Tech — Collision", "Summit Collision Center", "Columbus", "body", 65, 82, 4, "I-CAR Preferred", "Structural and panel repair on late-model vehicles in a climate-controlled facility."),
            ("EV Specialist Technician", "Precision Motors", "Columbus", "ev", 85, 110, 5, "EV Certification Required", "High-voltage diagnostics and repair across EV and hybrid platforms."),
            ("Lube & Tire Technician", "FastLane Service", "Columbus", "repair", 38, 48, 0, "Entry Level", "Oil changes, tire service and inspections with a structured training pathway."),
            ("Paint Technician", "Summit Collision Center", "Columbus", "paint", 60, 88, 6, "I-CAR Preferred", "Spray and color-match work in a modern downdraft booth."),
            ("Service Advisor / Estimator", "Apex Body & Auto", "Columbus", "estimator", 55, 90, 3, "Experience Required", "Write estimates, manage customer relationships and coordinate insurance work."),
            ("Diesel / Fleet Technician", "Apex Body & Auto", "Columbus", "diesel", 70, 98, 5, "ASE Preferred", "Maintain a mixed medium-duty fleet covering brakes, DPF and electrical."),
            ("General Service Technician", "Cleveland Auto Group", "Cleveland", "repair", 50, 72, 2, "ASE Preferred", "Dealer service role with an OEM training pathway."),
            ("Collision Estimator", "Cleveland Auto Group", "Cleveland", "estimator", 58, 95, 4, "I-CAR Required", "Blueprinting, supplement management and customer communication."),
            ("Transmission Specialist", "GearHead Transmissions", "Atlanta", "repair", 72, 105, 7, "ASE Required", "R&R and rebuild automatic and CVT units."),
            ("Mobile Repair Technician", "GearHead Transmissions", "Atlanta", "repair", 60, 85, 3, "ASE Preferred", "Independent mobile diagnostics and repair with company van and tools."),
            ("Apprentice Technician", "Dallas Drive Auto", "Dallas", "repair", 36, 50, 0, "Entry Level", "Paid apprenticeship with mentorship and ASE tuition assistance."),
        ]
        jobs = {}
        for title, company, metro, category, pay_min, pay_max, years, cert, description in rows:
            job, _ = Job.objects.update_or_create(
                employer=employers[company],
                title=title,
                defaults={
                    "city_pool": pools[metro],
                    "category": category,
                    "schedule": "full_time",
                    "pay_min": pay_min,
                    "pay_max": pay_max,
                    "experience_years": years,
                    "certification_requirement": cert,
                    "description": description,
                    "benefits": employers[company].perks,
                    "status": "active",
                },
            )
            jobs[title] = job
        return jobs

    def create_profiles(self, technicians):
        marcus = technicians["marcus@demo.wrenchlink.io"]
        jordan = technicians["jordan@demo.wrenchlink.io"]
        darnell = technicians["darnell@demo.wrenchlink.io"]

        certifications = [
            (
                marcus,
                "ASE Master Automobile Technician",
                "National Institute for Automotive Service Excellence",
                "ASE-MASTER-DEMO",
                date(2022, 6, 1),
                date(2027, 6, 1),
            ),
            (
                marcus,
                "ASE L3 Light Duty Hybrid / Electric Vehicle",
                "National Institute for Automotive Service Excellence",
                "ASE-L3-DEMO",
                date(2023, 3, 15),
                date(2028, 3, 15),
            ),
            (
                jordan,
                "I-CAR Platinum Individual",
                "I-CAR",
                "ICAR-DEMO",
                date(2024, 1, 10),
                date(2027, 1, 10),
            ),
            (
                darnell,
                "High Voltage Vehicle Safety",
                "EV Training Institute",
                "EV-HV-DEMO",
                date(2024, 8, 1),
                date(2027, 8, 1),
            ),
        ]
        for technician, name, issuer, credential_id, issued, expiry in certifications:
            Certification.objects.update_or_create(
                technician=technician,
                name=name,
                defaults={
                    "issuing_organization": issuer,
                    "credential_id": credential_id,
                    "issued_date": issued,
                    "expiry_date": expiry,
                    "status": Certification.Status.VERIFIED,
                    "is_verified": True,
                },
            )

        work_rows = [
            (
                marcus,
                "Northside Automotive",
                "Lead Diagnostic Technician",
                "Columbus, OH",
                date(2021, 4, 1),
                None,
                "Leads drivability, electrical, network and ADAS diagnostics while mentoring three developing technicians.",
            ),
            (
                marcus,
                "Midwest Motor Works",
                "Automotive Technician",
                "Dublin, OH",
                date(2017, 2, 1),
                date(2021, 3, 31),
                "Performed engine performance, HVAC, brake and steering repairs across domestic and Asian platforms.",
            ),
            (
                jordan,
                "Capital Collision",
                "Structural Repair Technician",
                "Columbus, OH",
                date(2019, 5, 1),
                None,
                "Completes structural pulls, panel replacement, welding and blueprint-driven repairs.",
            ),
        ]
        for technician, company, role, location, start, end, description in work_rows:
            WorkHistory.objects.update_or_create(
                technician=technician,
                company=company,
                role=role,
                defaults={
                    "location": location,
                    "start_date": start,
                    "end_date": end,
                    "description": description,
                },
            )

        education_rows = [
            (
                marcus,
                "Columbus State Community College",
                "Automotive Technology A.A.S.",
                2017,
            ),
            (
                marcus,
                "Bosch Training Center",
                "Advanced Vehicle Network Diagnostics",
                2023,
            ),
            (
                jordan,
                "Ohio Technical College",
                "Collision Repair and Refinishing",
                2019,
            ),
        ]
        for technician, school, program, completion_year in education_rows:
            Education.objects.update_or_create(
                technician=technician,
                school=school,
                program=program,
                defaults={"completion_year": completion_year},
            )

        ProfessionalReference.objects.update_or_create(
            technician=marcus,
            name="Dana Mitchell",
            relationship="Former Service Manager",
            defaults={
                "email": "dana.reference@example.com",
                "phone": "(555) 019-3010",
            },
        )
        ProfessionalReference.objects.update_or_create(
            technician=marcus,
            name="Luis Carter",
            relationship="Shop Foreman",
            defaults={
                "email": "luis.reference@example.com",
                "phone": "(555) 019-3011",
            },
        )

    def create_activity(self, technicians, jobs, employers):
        marcus = technicians["marcus@demo.wrenchlink.io"]
        jordan = technicians["jordan@demo.wrenchlink.io"]
        darnell = technicians["darnell@demo.wrenchlink.io"]
        sofia = technicians["sofia@demo.wrenchlink.io"]
        priya = technicians["priya@demo.wrenchlink.io"]
        apex = employers["Apex Body & Auto"]

        marcus_ev, _ = Application.objects.update_or_create(
            technician=marcus,
            job=jobs["EV Specialist Technician"],
            defaults={
                "stage": Application.Stage.INTERVIEW,
                "interview_at": timezone.now() + timedelta(days=3),
                "employer_notes": "Strong EV and diagnostic background.",
            },
        )
        jordan_body, _ = Application.objects.update_or_create(
            technician=jordan,
            job=jobs["Auto Body Repair Tech — Collision"],
            defaults={"stage": Application.Stage.REVIEWED},
        )
        marcus_offer, _ = Application.objects.update_or_create(
            technician=marcus,
            job=jobs["Master Technician — Diagnostics"],
            defaults={
                "stage": Application.Stage.OFFERED,
                "offer_details": "Proposed start date July 13, day shift, tool allowance included.",
                "employer_notes": "Top diagnostic candidate. References checked.",
            },
        )
        darnell_interview, _ = Application.objects.update_or_create(
            technician=darnell,
            job=jobs["Diesel / Fleet Technician"],
            defaults={
                "stage": Application.Stage.INTERVIEW,
                "interview_at": timezone.now() + timedelta(days=5),
                "employer_notes": "Discuss fleet electrical and DPF experience.",
            },
        )
        sofia_invite, _ = Application.objects.update_or_create(
            technician=sofia,
            job=jobs["Service Advisor / Estimator"],
            defaults={
                "stage": Application.Stage.INVITED,
                "invitation_message": "Your production and color-matching background could translate well to our blueprinting team.",
            },
        )
        priya_hired, _ = Application.objects.update_or_create(
            technician=priya,
            job=jobs["Diesel / Fleet Technician"],
            defaults={
                "stage": Application.Stage.HIRED,
                "offer_details": "Accepted full-time fleet technician position.",
                "employer_notes": "Hired after technical and team interviews.",
            },
        )
        Application.objects.update_or_create(
            technician=jordan,
            job=jobs["Service Advisor / Estimator"],
            defaults={"stage": Application.Stage.APPLIED},
        )

        message_rows = [
            (
                marcus_offer,
                apex.user,
                "Marcus, the team was impressed with your diagnostic process. We have added the offer details here.",
            ),
            (
                marcus_offer,
                marcus.user,
                "Thank you. I am reviewing the schedule and benefits and will respond shortly.",
            ),
            (
                darnell_interview,
                apex.user,
                "We would like to schedule a technical interview focused on fleet electrical diagnostics.",
            ),
            (
                darnell_interview,
                darnell.user,
                "That works for me. I can also walk through recent DPF and CAN network cases.",
            ),
            (
                marcus_ev,
                jobs["EV Specialist Technician"].employer.user,
                "Please bring examples of high-voltage isolation and battery diagnostic work.",
            ),
            (
                marcus_ev,
                marcus.user,
                "I will prepare two recent case studies for the interview.",
            ),
        ]
        for application, sender, body in message_rows:
            ApplicationMessage.objects.get_or_create(
                application=application, sender=sender, body=body
            )

        access_rows = [
            (
                apex,
                marcus,
                "all",
                CredentialAccessRequest.Status.APPROVED,
            ),
            (
                apex,
                darnell,
                "High Voltage Vehicle Safety",
                CredentialAccessRequest.Status.PENDING,
            ),
            (
                employers["Summit Collision Center"],
                jordan,
                "I-CAR Platinum Individual",
                CredentialAccessRequest.Status.APPROVED,
            ),
        ]
        for employer, technician, credential_type, status in access_rows:
            CredentialAccessRequest.objects.update_or_create(
                employer=employer,
                technician=technician,
                credential_type=credential_type,
                defaults={
                    "status": status,
                    "responded_at": (
                        timezone.now()
                        if status != CredentialAccessRequest.Status.PENDING
                        else None
                    ),
                },
            )

        TechnicianReview.objects.update_or_create(
            employer=apex,
            technician=priya,
            defaults={
                "skill": 5,
                "reliability": 5,
                "communication": 4,
                "comment": "Excellent diagnostic discipline and clear repair documentation.",
            },
        )
        EmployerReview.objects.update_or_create(
            technician=priya,
            employer=apex,
            defaults={
                "professionalism": 5,
                "communication": 4,
                "workplace": 5,
                "comment": "Organized onboarding, modern equipment, and clear expectations.",
            },
        )

        notification_rows = [
            (
                marcus.user,
                "Offer received",
                "Apex Body & Auto sent an offer for Master Technician — Diagnostics.",
                f"/applications/{marcus_offer.id}/",
                False,
            ),
            (
                marcus.user,
                "Interview scheduled",
                "Precision Motors scheduled your EV Specialist Technician interview.",
                f"/applications/{marcus_ev.id}/",
                False,
            ),
            (
                apex.user,
                "Candidate replied",
                "Marcus Thompson replied to your offer conversation.",
                f"/applications/{marcus_offer.id}/",
                False,
            ),
            (
                apex.user,
                "Interview confirmed",
                "Darnell Adams confirmed availability for an interview.",
                f"/applications/{darnell_interview.id}/",
                True,
            ),
            (
                sofia.user,
                "New job invitation",
                "Apex Body & Auto invited you to discuss Service Advisor / Estimator.",
                f"/applications/{sofia_invite.id}/",
                False,
            ),
        ]
        for recipient, title, body, link, is_read in notification_rows:
            Notification.objects.update_or_create(
                recipient=recipient,
                title=title,
                link=link,
                defaults={
                    "event": (
                        Notification.Event.OFFER
                        if "Offer" in title or "invitation" in title.lower()
                        else Notification.Event.APPLICATION
                    ),
                    "body": body,
                    "is_read": is_read,
                },
            )
            NotificationPreference.objects.get_or_create(user=recipient)

        SavedJob.objects.get_or_create(
            technician=marcus, job=jobs["Master Technician — Diagnostics"]
        )
        SavedJob.objects.get_or_create(
            technician=darnell, job=jobs["EV Specialist Technician"]
        )
