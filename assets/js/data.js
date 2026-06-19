/* ============================================================
   WRENCHLINK — seed data + localStorage store
   ============================================================ */

const WL_SEED_JOBS = [
  { id: 'j1', title: 'Master Technician — Diagnostics', shop: 'Apex Body & Auto', logo: 'AB', city: 'Westerville, OH', metro: 'Columbus', distance: 12, type: 'Auto Repair', schedule: 'Full-Time', payMin: 75, payMax: 95, cert: 'ASE Required', exp: 8, color: '#c2602b', desc: 'Lead diagnostic tech for a high-volume independent shop. Drivability, electrical, and ADAS calibration. Top pay for the right A-tech.' },
  { id: 'j2', title: 'Auto Body Repair Tech — Collision', shop: 'Summit Collision Center', logo: 'SC', city: 'Dublin, OH', metro: 'Columbus', distance: 18, type: 'Auto Body', schedule: 'Full-Time', payMin: 65, payMax: 82, cert: 'I-CAR Preferred', exp: 4, color: '#2f7d6b', desc: 'Structural and panel repair on late-model vehicles. I-CAR Gold shop with a clean, climate-controlled facility and modern frame equipment.' },
  { id: 'j3', title: 'EV Specialist Technician', shop: 'Precision Motors', logo: 'PM', city: 'Columbus, OH', metro: 'Columbus', distance: 5, type: 'Auto Repair', schedule: 'Full-Time', payMin: 85, payMax: 110, cert: 'EV Cert Required', exp: 5, color: '#5b4a6b', desc: 'High-voltage diagnostics and repair across EV/hybrid platforms. Manufacturer training provided. Must hold EV/Hybrid safety certification.' },
  { id: 'j4', title: 'Lube & Tire Technician', shop: 'FastLane Service', logo: 'FL', city: 'Hilliard, OH', metro: 'Columbus', distance: 14, type: 'Auto Repair', schedule: 'Part-Time', payMin: 38, payMax: 48, cert: 'Entry Level', exp: 0, color: '#357a8a', desc: 'Great entry point into the trade. Oil changes, tire service, inspections. We train and promote from within toward ASE certification.' },
  { id: 'j5', title: 'Paint Technician', shop: 'ColorWorks Refinish', logo: 'CW', city: 'Columbus, OH', metro: 'Columbus', distance: 7, type: 'Auto Body', schedule: 'Full-Time', payMin: 60, payMax: 88, cert: 'I-CAR Preferred', exp: 6, color: '#a8782f', desc: 'Spray and color-match in a downdraft booth environment. Waterborne experience a plus. Commission + base structure available.' },
  { id: 'j6', title: 'Service Advisor / Estimator', shop: 'Apex Body & Auto', logo: 'AB', city: 'Westerville, OH', metro: 'Columbus', distance: 12, type: 'Auto Body', schedule: 'Full-Time', payMin: 55, payMax: 90, cert: 'Experience Required', exp: 3, color: '#c2602b', desc: 'Write estimates, manage customer relationships, and coordinate with insurance. CCC/Mitchell experience preferred. Strong earning upside.' },
  { id: 'j7', title: 'Diesel / Fleet Technician', shop: 'Heartland Fleet Services', logo: 'HF', city: 'Grove City, OH', metro: 'Columbus', distance: 16, type: 'Auto Repair', schedule: 'Full-Time', payMin: 70, payMax: 98, cert: 'ASE Preferred', exp: 5, color: '#49546a', desc: 'Maintain a mixed medium-duty fleet. Brakes, DPF, electrical, and PM service. Tool allowance and boot stipend included.' },
  { id: 'j8', title: 'General Service Technician', shop: 'Cleveland Auto Group', logo: 'CA', city: 'Cleveland, OH', metro: 'Cleveland', distance: 4, type: 'Auto Repair', schedule: 'Full-Time', payMin: 50, payMax: 72, cert: 'ASE Preferred', exp: 2, color: '#3a6ea5', desc: 'Dealer service department seeking GS techs ready to grow. Flat-rate with guarantee, OEM training pathway, and modern equipment.' },
  { id: 'j9', title: 'Collision Estimator', shop: 'Lakeside Collision', logo: 'LC', city: 'Lakewood, OH', metro: 'Cleveland', distance: 9, type: 'Auto Body', schedule: 'Full-Time', payMin: 58, payMax: 95, cert: 'I-CAR Required', exp: 4, color: '#3f7d5a', desc: 'DRP-heavy shop seeks an experienced estimator. Blueprinting mindset, supplement management, and great communication skills.' },
  { id: 'j10', title: 'Transmission Specialist', shop: 'GearHead Transmissions', logo: 'GH', city: 'Atlanta, GA', metro: 'Atlanta', distance: 6, type: 'Auto Repair', schedule: 'Full-Time', payMin: 72, payMax: 105, cert: 'ASE Required', exp: 7, color: '#a8503c', desc: 'R&R and rebuild automatic and CVT units. Established shop with steady volume and a loyal customer base. Excellent flat-rate hours.' },
  { id: 'j11', title: 'Mobile Repair Technician', shop: 'OnSite Auto Care', logo: 'OS', city: 'Atlanta, GA', metro: 'Atlanta', distance: 11, type: 'Auto Repair', schedule: 'Full-Time', payMin: 60, payMax: 85, cert: 'ASE Preferred', exp: 3, color: '#2f7d6b', desc: 'Take the shop to the customer. Company van, tools, and tablet provided. Independent, self-directed work with strong hourly + bonus.' },
  { id: 'j12', title: 'Apprentice Technician', shop: 'Dallas Drive Auto', logo: 'DD', city: 'Dallas, TX', metro: 'Dallas', distance: 8, type: 'Auto Repair', schedule: 'Full-Time', payMin: 36, payMax: 50, cert: 'Entry Level', exp: 0, color: '#3f7d5a', desc: 'Paid apprenticeship with a clear path to A-tech. Mentorship, tuition assistance for ASE testing, and a supportive team culture.' },
];

const WL_SEED_CANDIDATES = [
  { id: 'c1', name: 'Marcus Thompson', role: 'Master Tech', exp: 9, metro: 'Columbus', city: 'Columbus, OH', tags: ['ASE Master','EV/Hybrid','Diagnostics'], rating: 4.9, reviews: 47, status: 'active', type: 'Auto Repair', color: '#c2602b', initials: 'MT' },
  { id: 'c2', name: 'Jordan Rivera', role: 'Collision / Body Tech', exp: 7, metro: 'Columbus', city: 'Dublin, OH', tags: ['I-CAR Gold','Frame Work','Paint Matching'], rating: 4.6, reviews: 31, status: 'passive', type: 'Auto Body', color: '#2f7d6b', initials: 'JR' },
  { id: 'c3', name: 'Darnell Adams', role: 'EV Specialist', exp: 5, metro: 'Columbus', city: 'Westerville, OH', tags: ['Tesla Certified','ASE L3 EV','ADAS'], rating: 4.8, reviews: 22, status: 'active', type: 'Auto Repair', color: '#5b4a6b', initials: 'DA' },
  { id: 'c4', name: 'Sofia Nguyen', role: 'Paint Technician', exp: 6, metro: 'Columbus', city: 'Columbus, OH', tags: ['Waterborne','Color Match','Downdraft'], rating: 4.7, reviews: 19, status: 'active', type: 'Auto Body', color: '#a8782f', initials: 'SN' },
  { id: 'c5', name: 'Tyler Brooks', role: 'General Service Tech', exp: 3, metro: 'Cleveland', city: 'Cleveland, OH', tags: ['ASE G1','Brakes','Suspension'], rating: 4.4, reviews: 12, status: 'active', type: 'Auto Repair', color: '#357a8a', initials: 'TB' },
  { id: 'c6', name: 'Maria Castillo', role: 'Estimator', exp: 8, metro: 'Cleveland', city: 'Lakewood, OH', tags: ['I-CAR Platinum','CCC One','Supplements'], rating: 4.9, reviews: 38, status: 'passive', type: 'Auto Body', color: '#c2602b', initials: 'MC' },
  { id: 'c7', name: 'Andre Wallace', role: 'Transmission Specialist', exp: 12, metro: 'Atlanta', city: 'Atlanta, GA', tags: ['ASE A2','CVT','Rebuild'], rating: 5.0, reviews: 54, status: 'active', type: 'Auto Repair', color: '#a8503c', initials: 'AW' },
  { id: 'c8', name: 'Priya Patel', role: 'Diesel / Fleet Tech', exp: 6, metro: 'Dallas', city: 'Dallas, TX', tags: ['ASE T-Series','DPF','Hydraulics'], rating: 4.7, reviews: 26, status: 'active', type: 'Auto Repair', color: '#3a6ea5', initials: 'PP' },
];

const WL_CITIES = [
  { name: 'Columbus', state: 'Ohio', region: 'Midwest', techs: 284, jobs: 67 },
  { name: 'Cleveland', state: 'Ohio', region: 'Midwest', techs: 319, jobs: 91 },
  { name: 'Atlanta', state: 'Georgia', region: 'Southeast', techs: 541, jobs: 148 },
  { name: 'Dallas', state: 'Texas', region: 'Southwest', techs: 723, jobs: 194 },
  { name: 'Chicago', state: 'Illinois', region: 'Midwest', techs: 891, jobs: 212 },
  { name: 'Phoenix', state: 'Arizona', region: 'Southwest', techs: 407, jobs: 103 },
  { name: 'Houston', state: 'Texas', region: 'Southwest', techs: 664, jobs: 177 },
  { name: 'Charlotte', state: 'N. Carolina', region: 'Southeast', techs: 318, jobs: 84 },
  { name: 'Detroit', state: 'Michigan', region: 'Midwest', techs: 612, jobs: 156 },
  { name: 'Tampa', state: 'Florida', region: 'Southeast', techs: 389, jobs: 97 },
  { name: 'Denver', state: 'Colorado', region: 'West', techs: 421, jobs: 110 },
  { name: 'Boston', state: 'Mass.', region: 'Northeast', techs: 356, jobs: 88 },
];

/* ── Store: localStorage-backed app state ── */
const WL = {
  KEY: 'wrenchlink_v1',
  _state: null,

  _default() {
    return {
      user: null,
      appliedJobs: [],
      savedJobs: [],
      userJobs: [],
      contacted: [],
      techStatus: 'active',
    };
  },

  load() {
    if (this._state) return this._state;
    try {
      const raw = localStorage.getItem(this.KEY);
      this._state = raw ? Object.assign(this._default(), JSON.parse(raw)) : this._default();
    } catch (e) {
      this._state = this._default();
    }
    return this._state;
  },

  save() {
    try { localStorage.setItem(this.KEY, JSON.stringify(this._state)); } catch (e) {}
  },

  get() { return this.load(); },
  set(patch) { Object.assign(this.load(), patch); this.save(); },

  allJobs() {
    const s = this.load();
    return [...s.userJobs, ...WL_SEED_JOBS];
  },
  candidates() { return WL_SEED_CANDIDATES; },
  cities() { return WL_CITIES; },

  isLoggedIn() { return !!this.load().user; },
  logout() { this.set({ user: null }); },

  toggleArray(key, id) {
    const s = this.load();
    const arr = s[key];
    const i = arr.indexOf(id);
    if (i === -1) arr.push(id); else arr.splice(i, 1);
    this.save();
    return arr.indexOf(id) !== -1;
  },
};
