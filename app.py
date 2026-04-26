from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import numpy as np
from scipy.linalg import eig
import os
from methods import MPE, BayesMethod, CPI, SAW, PROMETHEE, extract_alternative_values_from_comparisons

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ahp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'  # Required for session
db = SQLAlchemy(app)

# Models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    criteria = db.relationship('Criterion', backref='project', lazy=True, cascade="all, delete-orphan")
    alternatives = db.relationship('Alternative', backref='project', lazy=True, cascade="all, delete-orphan")

class Criterion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    comparisons = db.relationship('Comparison', backref='criterion', lazy=True, cascade="all, delete-orphan")

class Alternative(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

class Comparison(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id'), nullable=False)
    item1_id = db.Column(db.Integer, nullable=False)  # Could be criterion or alternative
    item2_id = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Float, nullable=False)  # 1/9 to 9
    type = db.Column(db.String(10), nullable=False)  # 'criteria' or 'alternatives'


# ==================== MODELS UNTUK SAW & PROMETHEE ====================

class CriterionType(db.Model):
    """Model untuk menyimpan tipe kriteria (Benefit/Cost) dan bobot untuk SAW/PROMETHEE"""
    id = db.Column(db.Integer, primary_key=True)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id', ondelete='CASCADE'), nullable=False, unique=True)
    criterion = db.relationship('Criterion', backref=db.backref('type_info', uselist=False, cascade='all, delete-orphan'))
    is_benefit = db.Column(db.Boolean, default=True)  # True = Benefit (Max), False = Cost (Min)
    weight_saw = db.Column(db.Float, default=1.0)  # Bobot untuk SAW (default 1.0)
    weight_promethee = db.Column(db.Float, default=1.0)  # Bobot untuk PROMETHEE
    
    def __repr__(self):
        return f"<CriterionType {self.criterion.name}>"


class PrometheeParameter(db.Model):
    """Model untuk menyimpan parameter PROMETHEE (p, q) per kriteria"""
    id = db.Column(db.Integer, primary_key=True)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id', ondelete='CASCADE'), nullable=False, unique=True)
    criterion = db.relationship('Criterion', backref=db.backref('promethee_param', uselist=False, cascade='all, delete-orphan'))
    p_threshold = db.Column(db.Float, default=0.5)  # Preference threshold
    q_threshold = db.Column(db.Float, default=0.1)  # Indifference threshold
    
    def __repr__(self):
        return f"<PrometheeParameter C{self.criterion_id} p={self.p_threshold}>"

# AHP Functions
def calculate_weights(matrix):
    eigenvalues, eigenvectors = eig(matrix)
    max_eigenvalue = np.real(eigenvalues[np.argmax(np.real(eigenvalues))])
    weights = np.real(eigenvectors[:, np.argmax(np.real(eigenvalues))])
    weights = weights / np.sum(weights)
    return weights, max_eigenvalue

def consistency_index(lambda_max, n):
    RI = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
    if n <= 2:
        return 0.0
    if n - 1 == 0 or RI.get(n, 1.49) == 0:
        return 0.0
    return (lambda_max - n) / (n - 1) / RI.get(n, 1.49)


HYBRID_STAGE1_LABELS = {
    'mpe': 'MPE',
    'bayes': 'Bayes',
    'cpi': 'CPI'
}

HYBRID_STAGE2_LABELS = {
    'ahp': 'AHP',
    'saw': 'SAW',
    'promethee': 'PROMETHEE II'
}


def build_criteria_matrix(criteria):
    n_crit = len(criteria)
    criterion_ids = [crit.id for crit in criteria]
    crit_matrix = np.ones((n_crit, n_crit))

    for comp in Comparison.query.filter(
        Comparison.type == 'criteria',
        Comparison.criterion_id.in_(criterion_ids)
    ).all():
        if comp.item1_id < n_crit and comp.item2_id < n_crit:
            crit_matrix[comp.item1_id, comp.item2_id] = comp.value
            crit_matrix[comp.item2_id, comp.item1_id] = 1 / comp.value

    return crit_matrix


def get_project_analysis_data(project):
    criteria = project.criteria
    alternatives = project.alternatives

    if len(criteria) == 0 or len(alternatives) == 0:
        return None

    crit_matrix = build_criteria_matrix(criteria)
    crit_weights, lambda_crit = calculate_weights(crit_matrix)
    alt_values = extract_alternative_values_from_comparisons(project, criteria, Comparison)

    return {
        'criteria': criteria,
        'alternatives': alternatives,
        'crit_matrix': crit_matrix,
        'crit_weights': crit_weights,
        'lambda_crit': lambda_crit,
        'ci_crit': consistency_index(lambda_crit, len(criteria)),
        'alt_values': alt_values
    }


def get_stage_one_scores(stage1_method, crit_weights, alt_values):
    if stage1_method == 'mpe':
        scores = MPE.calculate_scores(crit_weights, alt_values)
        score_label = 'Skor MPE'
    elif stage1_method == 'bayes':
        bayes_result = BayesMethod.calculate_expected_values(crit_weights, alt_values)
        scores = bayes_result['expected_values']
        score_label = 'Expected Value Bayes'
    elif stage1_method == 'cpi':
        cpi_report = CPI.calculate_full_cpi_report(crit_weights, alt_values)
        scores = cpi_report['average']
        score_label = 'Skor CPI Rata-rata'
    else:
        raise ValueError('Metode tahap 1 tidak valid')

    return np.asarray(scores, dtype=float), score_label


def format_ranked_scores(alternatives, scores, score_key='score'):
    ranked = []
    for i, alt in enumerate(alternatives):
        ranked.append({
            'id': alt.id,
            'name': alt.name,
            score_key: float(scores[i]),
            'rank': i + 1
        })

    ranked.sort(key=lambda item: item[score_key], reverse=True)
    for rank, item in enumerate(ranked, start=1):
        item['rank'] = rank
    return ranked


def get_saw_configs(criteria):
    configs = []
    created = False

    for crit in criteria:
        crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
        if not crit_type:
            crit_type = CriterionType(criterion_id=crit.id, is_benefit=True, weight_saw=1.0)
            db.session.add(crit_type)
            created = True

        configs.append({
            'criterion': crit,
            'is_benefit': crit_type.is_benefit,
            'weight': crit_type.weight_saw
        })

    if created:
        db.session.commit()

    return configs


def get_promethee_configs(criteria):
    criterion_configs = []
    promethee_params = []
    created = False

    for crit in criteria:
        crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
        if not crit_type:
            crit_type = CriterionType(criterion_id=crit.id, is_benefit=True, weight_promethee=1.0)
            db.session.add(crit_type)
            created = True

        prom_param = PrometheeParameter.query.filter_by(criterion_id=crit.id).first()
        if not prom_param:
            prom_param = PrometheeParameter(criterion_id=crit.id, p_threshold=0.5, q_threshold=0.1)
            db.session.add(prom_param)
            created = True

        criterion_configs.append({
            'criterion': crit,
            'is_benefit': crit_type.is_benefit,
            'weight': crit_type.weight_promethee
        })
        promethee_params.append({
            'criterion_id': crit.id,
            'p': prom_param.p_threshold,
            'q': prom_param.q_threshold
        })

    if created:
        db.session.commit()

    return criterion_configs, promethee_params


def calculate_ahp_for_selected_alternatives(criteria, alternatives, selected_indices):
    selected_alternatives = [alternatives[idx] for idx in selected_indices]
    n_crit = len(criteria)
    n_alt = len(selected_indices)

    crit_matrix = build_criteria_matrix(criteria)
    crit_weights, lambda_crit = calculate_weights(crit_matrix)
    ci_crit = consistency_index(lambda_crit, n_crit)

    local_index_map = {original_idx: local_idx for local_idx, original_idx in enumerate(selected_indices)}
    alt_weights = []

    for crit in criteria:
        alt_matrix = np.ones((n_alt, n_alt))
        comparisons = Comparison.query.filter_by(criterion_id=crit.id, type='alternatives').all()

        for comp in comparisons:
            if comp.item1_id in local_index_map and comp.item2_id in local_index_map:
                local_i = local_index_map[comp.item1_id]
                local_j = local_index_map[comp.item2_id]
                alt_matrix[local_i, local_j] = comp.value
                alt_matrix[local_j, local_i] = 1 / comp.value

        weights, _ = calculate_weights(alt_matrix)
        alt_weights.append(weights)

    alt_weights = np.array(alt_weights).T
    overall_scores = alt_weights @ crit_weights
    results = format_ranked_scores(selected_alternatives, overall_scores)

    return {
        'results': results,
        'score_label': 'Skor AHP',
        'details': {
            'ci_crit': ci_crit
        }
    }


def calculate_stage_two_results(stage2_method, criteria, alternatives, selected_indices, alt_values):
    selected_alternatives = [alternatives[idx] for idx in selected_indices]
    selected_matrix = alt_values[selected_indices, :]

    if stage2_method == 'ahp':
        return calculate_ahp_for_selected_alternatives(criteria, alternatives, selected_indices)

    if stage2_method == 'saw':
        criterion_configs = get_saw_configs(criteria)
        saw_engine = SAW(selected_matrix, [cfg['is_benefit'] for cfg in criterion_configs])
        saw_result = saw_engine.calculate(np.array([cfg['weight'] for cfg in criterion_configs]))
        results = format_ranked_scores(selected_alternatives, saw_result['final_scores'])
        return {
            'results': results,
            'score_label': 'Skor SAW',
            'details': {
                'criterion_configs': criterion_configs
            }
        }

    if stage2_method == 'promethee':
        criterion_configs, promethee_params = get_promethee_configs(criteria)
        prom_engine = PROMETHEE(selected_matrix, [cfg['is_benefit'] for cfg in criterion_configs])
        prom_result = prom_engine.calculate(
            np.array([cfg['weight'] for cfg in criterion_configs]),
            [(param['p'], param['q']) for param in promethee_params]
        )

        results = []
        for i, alt in enumerate(selected_alternatives):
            results.append({
                'id': alt.id,
                'name': alt.name,
                'score': float(prom_result['phi_net'][i]),
                'rank': int(prom_result['rankings'][i]),
                'phi_plus': float(prom_result['phi_plus'][i]),
                'phi_minus': float(prom_result['phi_minus'][i])
            })
        results.sort(key=lambda item: item['rank'])

        return {
            'results': results,
            'score_label': 'Net Flow PROMETHEE',
            'details': {
                'criterion_configs': criterion_configs,
                'promethee_params': promethee_params
            }
        }

    raise ValueError('Metode tahap 2 tidak valid')

# Routes
@app.route('/')
def index():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if request.method == 'POST':
        name = request.form['name']
        project = Project(name=name)
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project.id))
    return render_template('create_project.html')

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)


@app.route('/project/<int:project_id>/hybrid_input', methods=['GET', 'POST'])
def hybrid_input(project_id):
    project = Project.query.get_or_404(project_id)
    analysis_data = get_project_analysis_data(project)

    if analysis_data is None:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')

    if len(analysis_data['alternatives']) < 2:
        return render_template('error.html', message='Model hybrid membutuhkan minimal 2 alternatif')

    if request.method == 'POST':
        stage1_method = request.form.get('stage1_method', 'mpe')
        stage2_method = request.form.get('stage2_method', 'ahp')
        top_n = int(request.form.get('top_n', len(analysis_data['alternatives'])))

        return redirect(url_for(
            'hybrid_results',
            project_id=project_id,
            stage1=stage1_method,
            stage2=stage2_method,
            top_n=top_n
        ))

    return render_template(
        'hybrid_input.html',
        project=project,
        stage1_options=HYBRID_STAGE1_LABELS,
        stage2_options=HYBRID_STAGE2_LABELS,
        max_top_n=len(analysis_data['alternatives'])
    )


@app.route('/project/<int:project_id>/hybrid_results')
def hybrid_results(project_id):
    project = Project.query.get_or_404(project_id)
    analysis_data = get_project_analysis_data(project)

    if analysis_data is None:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')

    criteria = analysis_data['criteria']
    alternatives = analysis_data['alternatives']
    n_alt = len(alternatives)

    stage1_method = request.args.get('stage1', 'mpe')
    stage2_method = request.args.get('stage2', 'ahp')
    requested_top_n = request.args.get('top_n', n_alt)

    try:
        top_n = int(requested_top_n)
    except (TypeError, ValueError):
        top_n = n_alt

    top_n = max(2, min(top_n, n_alt))

    if stage1_method not in HYBRID_STAGE1_LABELS or stage2_method not in HYBRID_STAGE2_LABELS:
        return render_template('error.html', message='Konfigurasi metode hybrid tidak valid')

    stage1_scores, stage1_score_label = get_stage_one_scores(
        stage1_method,
        analysis_data['crit_weights'],
        analysis_data['alt_values']
    )

    stage1_results = format_ranked_scores(alternatives, stage1_scores)
    selected_stage1_results = stage1_results[:top_n]
    selected_alt_ids = {item['id'] for item in selected_stage1_results}
    selected_indices = [idx for idx, alt in enumerate(alternatives) if alt.id in selected_alt_ids]

    stage2_data = calculate_stage_two_results(
        stage2_method,
        criteria,
        alternatives,
        selected_indices,
        analysis_data['alt_values']
    )

    return render_template(
        'hybrid_results.html',
        project=project,
        stage1_method=stage1_method,
        stage2_method=stage2_method,
        stage1_label=HYBRID_STAGE1_LABELS[stage1_method],
        stage2_label=HYBRID_STAGE2_LABELS[stage2_method],
        stage1_results=stage1_results,
        selected_stage1_results=selected_stage1_results,
        stage1_score_label=stage1_score_label,
        stage2_results=stage2_data['results'],
        stage2_score_label=stage2_data['score_label'],
        stage2_details=stage2_data['details'],
        top_n=top_n
    )

@app.route('/project/<int:project_id>/add_criteria', methods=['GET', 'POST'])
def add_criteria(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        names = request.form.getlist('criteria')
        for name in names:
            if name:
                criterion = Criterion(name=name, project=project)
                db.session.add(criterion)
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project_id))
    return render_template('add_criteria.html', project=project)

@app.route('/project/<int:project_id>/add_alternatives', methods=['GET', 'POST'])
def add_alternatives(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        names = request.form.getlist('alternatives')
        for name in names:
            if name:
                alternative = Alternative(name=name, project=project)
                db.session.add(alternative)
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project_id))
    return render_template('add_alternatives.html', project=project)

@app.route('/project/<int:project_id>/compare_criteria', methods=['GET', 'POST'])
def compare_criteria(project_id):
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    n = len(criteria)
    if request.method == 'POST':
        for i in range(n):
            for j in range(i+1, n):
                value = float(request.form[f'comp_{i}_{j}'])
                comp = Comparison(criterion_id=criteria[i].id, item1_id=i, item2_id=j, value=value, type='criteria')
                db.session.add(comp)
                # Add reciprocal
                comp_recip = Comparison(criterion_id=criteria[i].id, item1_id=j, item2_id=i, value=1/value, type='criteria')
                db.session.add(comp_recip)
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project_id))
    return render_template('compare_criteria.html', project=project, criteria=criteria)

@app.route('/project/<int:project_id>/compare_alternatives/<int:criterion_id>', methods=['GET', 'POST'])
def compare_alternatives(project_id, criterion_id):
    project = Project.query.get_or_404(project_id)
    criterion = Criterion.query.get_or_404(criterion_id)
    alternatives = project.alternatives
    n = len(alternatives)
    if request.method == 'POST':
        for i in range(n):
            for j in range(i+1, n):
                value = float(request.form[f'comp_{i}_{j}'])
                comp = Comparison(criterion_id=criterion_id, item1_id=i, item2_id=j, value=value, type='alternatives')
                db.session.add(comp)
                comp_recip = Comparison(criterion_id=criterion_id, item1_id=j, item2_id=i, value=1/value, type='alternatives')
                db.session.add(comp_recip)
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project_id))
    return render_template('compare_alternatives.html', project=project, criterion=criterion, alternatives=alternatives)

@app.route('/project/<int:project_id>/results')
def results(project_id):
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    n_crit = len(criteria)
    n_alt = len(alternatives)
    
    if n_crit == 0 or n_alt == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')

    criterion_ids = [crit.id for crit in criteria]

    # Build criteria matrix
    crit_matrix = np.ones((n_crit, n_crit))
    for comp in Comparison.query.filter(Comparison.type == 'criteria', Comparison.criterion_id.in_(criterion_ids)).all():
        if comp.item1_id < n_crit and comp.item2_id < n_crit:
            crit_matrix[comp.item1_id, comp.item2_id] = comp.value
            crit_matrix[comp.item2_id, comp.item1_id] = 1/comp.value
    
    crit_weights, lambda_crit = calculate_weights(crit_matrix)
    ci_crit = consistency_index(lambda_crit, n_crit)
    
    # Alternative matrices for each criterion
    alt_weights = []
    for crit in criteria:
        alt_matrix = np.ones((n_alt, n_alt))
        for comp in Comparison.query.filter_by(criterion_id=crit.id, type='alternatives').all():
            alt_matrix[comp.item1_id, comp.item2_id] = comp.value
            alt_matrix[comp.item2_id, comp.item1_id] = 1/comp.value
        weights, _ = calculate_weights(alt_matrix)
        alt_weights.append(weights)
    
    alt_weights = np.array(alt_weights).T  # Shape: (n_alt, n_crit)
    
    # Overall scores
    overall_scores = alt_weights @ crit_weights
    
    results = []
    for i, alt in enumerate(alternatives):
        results.append({'name': alt.name, 'score': overall_scores[i]})
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return render_template('results.html', project=project, results=results, ci_crit=ci_crit)


# ==================== ROUTES UNTUK METODE TAMBAHAN ====================

@app.route('/project/<int:project_id>/mpe_results')
def mpe_results(project_id):
    """Route untuk Metode Perbandingan Eksponensial (MPE)"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    n_crit = len(criteria)
    n_alt = len(alternatives)
    
    if n_crit == 0 or n_alt == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    # Build criteria matrix dan hitung weights
    criterion_ids = [crit.id for crit in criteria]
    crit_matrix = np.ones((n_crit, n_crit))
    for comp in Comparison.query.filter(Comparison.type == 'criteria', Comparison.criterion_id.in_(criterion_ids)).all():
        crit_matrix[comp.item1_id, comp.item2_id] = comp.value
        crit_matrix[comp.item2_id, comp.item1_id] = 1/comp.value
    
    crit_weights, _ = calculate_weights(crit_matrix)
    
    # Ambil nilai alternatif dari perbandingan
    alt_values = extract_alternative_values_from_comparisons(project, criteria, Comparison)
    
    # Hitung MPE scores
    mpe_basic = MPE.calculate_scores(crit_weights, alt_values)
    mpe_advanced = MPE.calculate_scores_advanced(crit_weights, alt_values)
    
    # Format results
    results_basic = []
    results_advanced = []
    for i, alt in enumerate(alternatives):
        results_basic.append({'name': alt.name, 'score': mpe_basic[i]})
        results_advanced.append({'name': alt.name, 'score': mpe_advanced[i]})
    
    results_basic.sort(key=lambda x: x['score'], reverse=True)
    results_advanced.sort(key=lambda x: x['score'], reverse=True)
    
    return render_template('mpe_results.html', 
                         project=project, 
                         results_basic=results_basic,
                         results_advanced=results_advanced)


@app.route('/project/<int:project_id>/bayes_results')
def bayes_results(project_id):
    """Route untuk Teorema Bayes dengan Pendekatan Nilai Harapan"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    n_crit = len(criteria)
    n_alt = len(alternatives)
    
    if n_crit == 0 or n_alt == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    # Build criteria matrix dan hitung weights
    criterion_ids = [crit.id for crit in criteria]
    crit_matrix = np.ones((n_crit, n_crit))
    for comp in Comparison.query.filter(Comparison.type == 'criteria', Comparison.criterion_id.in_(criterion_ids)).all():
        crit_matrix[comp.item1_id, comp.item2_id] = comp.value
        crit_matrix[comp.item2_id, comp.item1_id] = 1/comp.value
    
    crit_weights, _ = calculate_weights(crit_matrix)
    
    # Ambil nilai alternatif
    alt_values = extract_alternative_values_from_comparisons(project, criteria, Comparison)
    
    # Hitung Bayes results
    bayes_result = BayesMethod.calculate_expected_values(crit_weights, alt_values)
    
    # Format results
    results = []
    for i, alt in enumerate(alternatives):
        results.append({
            'name': alt.name,
            'posterior': bayes_result['posterior'][i],
            'expected_value': bayes_result['expected_values'][i],
            'prior': bayes_result['prior'][i]
        })
    
    results.sort(key=lambda x: x['expected_value'], reverse=True)
    
    return render_template('bayes_results.html', 
                         project=project, 
                         results=results,
                         bayes_summary={
                             'avg_posterior': np.mean(bayes_result['posterior']),
                             'max_posterior': np.max(bayes_result['posterior']),
                             'min_posterior': np.min(bayes_result['posterior'])
                         })


@app.route('/project/<int:project_id>/cpi_results')
def cpi_results(project_id):
    """Route untuk Composite Performance Index (CPI)"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    n_crit = len(criteria)
    n_alt = len(alternatives)
    
    if n_crit == 0 or n_alt == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    # Build criteria matrix dan hitung weights
    criterion_ids = [crit.id for crit in criteria]
    crit_matrix = np.ones((n_crit, n_crit))
    for comp in Comparison.query.filter(Comparison.type == 'criteria', Comparison.criterion_id.in_(criterion_ids)).all():
        crit_matrix[comp.item1_id, comp.item2_id] = comp.value
        crit_matrix[comp.item2_id, comp.item1_id] = 1/comp.value
    
    crit_weights, _ = calculate_weights(crit_matrix)
    
    # Ambil nilai alternatif
    alt_values = extract_alternative_values_from_comparisons(project, criteria, Comparison)
    
    # Hitung semua CPI methods
    cpi_report = CPI.calculate_full_cpi_report(crit_weights, alt_values)
    
    # Format results untuk setiap metode
    results_data = {}
    for method_name, scores in cpi_report.items():
        results = []
        for i, alt in enumerate(alternatives):
            results.append({'name': alt.name, 'score': scores[i]})
        results.sort(key=lambda x: x['score'], reverse=True)
        results_data[method_name] = results
    
    # Hitung consistency for average CPI
    consistency = CPI.calculate_consistency_measure(cpi_report['average'])
    
    return render_template('cpi_results.html', 
                         project=project,
                         results_data=results_data,
                         consistency=consistency,
                         criteria=criteria,
                         alternatives=alternatives)


@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('index'))


# ==================== ROUTES UNTUK SAW (Simple Additive Weighting) ====================

@app.route('/project/<int:project_id>/saw_input', methods=['GET', 'POST'])
def saw_input(project_id):
    """Route untuk input bobot dan tipe kriteria untuk SAW"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    
    if len(criteria) == 0 or len(alternatives) == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    if request.method == 'POST':
        # Simpan tipe kriteria dan bobot
        for crit in criteria:
            is_benefit = request.form.get(f'type_{crit.id}') == 'benefit'
            weight = float(request.form.get(f'weight_{crit.id}', 1.0))
            
            # Update atau create CriterionType
            crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
            if not crit_type:
                crit_type = CriterionType(criterion_id=crit.id, is_benefit=is_benefit, weight_saw=weight)
                db.session.add(crit_type)
            else:
                crit_type.is_benefit = is_benefit
                crit_type.weight_saw = weight
        
        db.session.commit()
        return redirect(url_for('saw_results', project_id=project_id))
    
    # Ambil data yang sudah ada
    criterion_data = []
    for crit in criteria:
        crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
        criterion_data.append({
            'criterion': crit,
            'is_benefit': crit_type.is_benefit if crit_type else True,
            'weight': crit_type.weight_saw if crit_type else 1.0
        })
    
    return render_template('saw_input.html', project=project, criterion_data=criterion_data, alternatives=alternatives)


@app.route('/project/<int:project_id>/saw_results')
def saw_results(project_id):
    """Route untuk hasil perhitungan SAW"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    
    if len(criteria) == 0 or len(alternatives) == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    # Ambil data kriteria
    criterion_configs = []
    for crit in criteria:
        crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
        if not crit_type:
            crit_type = CriterionType(criterion_id=crit.id, is_benefit=True, weight_saw=1.0)
            db.session.add(crit_type)
        criterion_configs.append({
            'criterion': crit,
            'is_benefit': crit_type.is_benefit,
            'weight': crit_type.weight_saw
        })
    db.session.commit()
    
    # Ambil nilai alternatif
    alt_values = extract_alternative_values_from_comparisons(project, criteria, Comparison)
    
    # Jika semua nilai 0, gunakan nilai default
    if np.all(alt_values == 0):
        alt_values = np.random.rand(len(alternatives), len(criteria)) * 9 + 1
    
    # Hitung SAW
    saw_engine = SAW(alt_values, [cfg['is_benefit'] for cfg in criterion_configs])
    saw_results = saw_engine.calculate(np.array([cfg['weight'] for cfg in criterion_configs]))
    
    # Format results
    results = []
    for i, alt in enumerate(alternatives):
        results.append({
            'name': alt.name,
            'score': saw_results['final_scores'][i],
            'rank': saw_results['rankings'][i]
        })
    
    results.sort(key=lambda x: x['rank'])
    
    return render_template('saw_results.html', 
                         project=project,
                         results=results,
                         normalized_matrix=saw_results['normalized_matrix'].tolist(),
                         weighted_matrix=saw_results['weighted_matrix'].tolist(),
                         final_scores=saw_results['final_scores'].tolist(),
                         criteria=criteria,
                         alternatives=alternatives,
                         criterion_configs=criterion_configs)


# ==================== ROUTES UNTUK PROMETHEE II ====================

@app.route('/project/<int:project_id>/promethee_input', methods=['GET', 'POST'])
def promethee_input(project_id):
    """Route untuk input parameter PROMETHEE"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    
    if len(criteria) == 0 or len(alternatives) == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    if request.method == 'POST':
        # Simpan parameter PROMETHEE
        for crit in criteria:
            is_benefit = request.form.get(f'type_{crit.id}') == 'benefit'
            weight = float(request.form.get(f'weight_{crit.id}', 1.0))
            p_threshold = float(request.form.get(f'p_{crit.id}', 0.5))
            q_threshold = float(request.form.get(f'q_{crit.id}', 0.1))
            
            # Update atau create CriterionType
            crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
            if not crit_type:
                crit_type = CriterionType(criterion_id=crit.id, is_benefit=is_benefit, weight_promethee=weight)
                db.session.add(crit_type)
            else:
                crit_type.is_benefit = is_benefit
                crit_type.weight_promethee = weight
            
            # Update atau create PrometheeParameter
            prom_param = PrometheeParameter.query.filter_by(criterion_id=crit.id).first()
            if not prom_param:
                prom_param = PrometheeParameter(criterion_id=crit.id, p_threshold=p_threshold, q_threshold=q_threshold)
                db.session.add(prom_param)
            else:
                prom_param.p_threshold = p_threshold
                prom_param.q_threshold = q_threshold
        
        db.session.commit()
        return redirect(url_for('promethee_results', project_id=project_id))
    
    # Ambil data yang sudah ada
    criterion_data = []
    for crit in criteria:
        crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
        prom_param = PrometheeParameter.query.filter_by(criterion_id=crit.id).first()
        criterion_data.append({
            'criterion': crit,
            'is_benefit': crit_type.is_benefit if crit_type else True,
            'weight': crit_type.weight_promethee if crit_type else 1.0,
            'p_threshold': prom_param.p_threshold if prom_param else 0.5,
            'q_threshold': prom_param.q_threshold if prom_param else 0.1
        })
    
    return render_template('promethee_input.html', project=project, criterion_data=criterion_data, alternatives=alternatives)


@app.route('/project/<int:project_id>/promethee_results')
def promethee_results(project_id):
    """Route untuk hasil perhitungan PROMETHEE II"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    
    if len(criteria) == 0 or len(alternatives) == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    # Ambil data kriteria
    criterion_configs = []
    promethee_params = []
    for crit in criteria:
        crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
        if not crit_type:
            crit_type = CriterionType(criterion_id=crit.id, is_benefit=True, weight_promethee=1.0)
            db.session.add(crit_type)
        
        prom_param = PrometheeParameter.query.filter_by(criterion_id=crit.id).first()
        if not prom_param:
            prom_param = PrometheeParameter(criterion_id=crit.id, p_threshold=0.5, q_threshold=0.1)
            db.session.add(prom_param)
        
        criterion_configs.append({
            'criterion': crit,
            'is_benefit': crit_type.is_benefit,
            'weight': crit_type.weight_promethee
        })
        promethee_params.append({
            'criterion_id': crit.id,
            'p': prom_param.p_threshold,
            'q': prom_param.q_threshold
        })
    db.session.commit()
    
    # Ambil nilai alternatif
    alt_values = extract_alternative_values_from_comparisons(project, criteria, Comparison)
    
    # Jika semua nilai 0, gunakan nilai default
    if np.all(alt_values == 0):
        alt_values = np.random.rand(len(alternatives), len(criteria)) * 9 + 1
    
    # Hitung PROMETHEE
    prom_engine = PROMETHEE(alt_values, [cfg['is_benefit'] for cfg in criterion_configs])
    prom_results = prom_engine.calculate(
        np.array([cfg['weight'] for cfg in criterion_configs]),
        [(p['p'], p['q']) for p in promethee_params]
    )
    
    # Format results
    results = []
    for i, alt in enumerate(alternatives):
        results.append({
            'name': alt.name,
            'phi_plus': prom_results['phi_plus'][i],
            'phi_minus': prom_results['phi_minus'][i],
            'phi_net': prom_results['phi_net'][i],
            'rank': prom_results['rankings'][i]
        })
    
    results.sort(key=lambda x: x['rank'])
    
    return render_template('promethee_results.html',
                         project=project,
                         results=results,
                         criteria=criteria,
                         alternatives=alternatives,
                         criterion_configs=criterion_configs,
                         promethee_params=promethee_params,
                         prom_details=prom_results)


# ==================== ROUTE PERBANDINGAN METODE ====================

@app.route('/project/<int:project_id>/method_comparison')
def method_comparison(project_id):
    """Route untuk perbandingan hasil SAW vs PROMETHEE II"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    
    if len(criteria) == 0 or len(alternatives) == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    # Ambil nilai alternatif
    alt_values = extract_alternative_values_from_comparisons(project, criteria, Comparison)
    
    if np.all(alt_values == 0):
        alt_values = np.random.rand(len(alternatives), len(criteria)) * 9 + 1
    
    # Ambil konfigurasi kriteria
    criterion_configs = []
    promethee_params = []
    for crit in criteria:
        crit_type = CriterionType.query.filter_by(criterion_id=crit.id).first()
        if not crit_type:
            crit_type = CriterionType(criterion_id=crit.id, is_benefit=True, 
                                     weight_saw=1.0, weight_promethee=1.0)
            db.session.add(crit_type)
        
        prom_param = PrometheeParameter.query.filter_by(criterion_id=crit.id).first()
        if not prom_param:
            prom_param = PrometheeParameter(criterion_id=crit.id, p_threshold=0.5, q_threshold=0.1)
            db.session.add(prom_param)
        
        criterion_configs.append({
            'criterion': crit,
            'is_benefit': crit_type.is_benefit,
            'weight_saw': crit_type.weight_saw,
            'weight_promethee': crit_type.weight_promethee
        })
        promethee_params.append({
            'criterion_id': crit.id,
            'p': prom_param.p_threshold,
            'q': prom_param.q_threshold
        })
    db.session.commit()
    
    # Hitung SAW
    saw_engine = SAW(alt_values, [cfg['is_benefit'] for cfg in criterion_configs])
    saw_results = saw_engine.calculate(np.array([cfg['weight_saw'] for cfg in criterion_configs]))
    
    # Hitung PROMETHEE
    prom_engine = PROMETHEE(alt_values, [cfg['is_benefit'] for cfg in criterion_configs])
    prom_results = prom_engine.calculate(
        np.array([cfg['weight_promethee'] for cfg in criterion_configs]),
        [(p['p'], p['q']) for p in promethee_params]
    )
    
    # Format results untuk perbandingan
    comparison_results = []
    for i, alt in enumerate(alternatives):
        comparison_results.append({
            'name': alt.name,
            'saw_score': saw_results['final_scores'][i],
            'saw_rank': saw_results['rankings'][i],
            'promethee_phi': prom_results['phi_net'][i],
            'promethee_rank': prom_results['rankings'][i],
            'saw_phi_plus': prom_results['phi_plus'][i],
            'saw_phi_minus': prom_results['phi_minus'][i],
            'saw_bar': min(float(saw_results['final_scores'][i]) * 100, 100),
            'promethee_bar': min(abs(float(prom_results['phi_net'][i])) * 100, 100)
        })

    consistent_items = [result['name'] for result in comparison_results if result['saw_rank'] == result['promethee_rank']]
    max_diff = max((abs(result['saw_rank'] - result['promethee_rank']) for result in comparison_results), default=0)

    return render_template('comparison_results.html',
                         project=project,
                         comparison_results=comparison_results,
                         criteria=criteria,
                         alternatives=alternatives,
                         consistent_items=consistent_items,
                         max_diff=max_diff)


# ==================== ROUTE YAGER KMKK ====================

@app.route('/project/<int:project_id>/yager_input', methods=['GET', 'POST'])
def yager_input(project_id):
    """Route untuk input bobot kriteria dan penilaian pakar untuk Yager KMKK"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    
    if len(criteria) == 0 or len(alternatives) == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    # Skala kualitatif untuk dropdown
    scale_options = [
        {'value': 7, 'label': 'S (Sempurna)'},
        {'value': 6, 'label': 'SB (Sangat Baik)'},
        {'value': 5, 'label': 'B (Baik)'},
        {'value': 4, 'label': 'Sd (Sedang)'},
        {'value': 3, 'label': 'K (Kurang)'},
        {'value': 2, 'label': 'SK (Sangat Kurang)'},
        {'value': 1, 'label': 'BS (Buruk Sekali)'}
    ]
    
    if request.method == 'POST':
        # Ambil jumlah pakar
        num_experts = int(request.form.get('num_experts', 3))
        
        # Simpan bobot kriteria
        criteria_weights = {}
        for crit in criteria:
            weight = int(request.form.get(f'weight_{crit.id}', 4))  # Default Sedang
            criteria_weights[crit.id] = weight
        
        # Simpan penilaian pakar
        expert_ratings = {}
        for i in range(1, num_experts + 1):
            expert_ratings[f'PK{i}'] = {}
            for alt in alternatives:
                expert_ratings[f'PK{i}'][alt.id] = {}
                for crit in criteria:
                    rating = int(request.form.get(f'rating_PK{i}_{alt.id}_{crit.id}', 4))
                    expert_ratings[f'PK{i}'][alt.id][crit.id] = rating
        
        # Simpan ke session untuk digunakan di results
        session['yager_data'] = {
            'criteria_weights': criteria_weights,
            'expert_ratings': expert_ratings,
            'num_experts': num_experts,
            'project_id': project_id
        }
        
        return redirect(url_for('yager_results', project_id=project_id))
    
    # Ambil data yang sudah ada dari session jika ada
    yager_data = session.get('yager_data', {})
    saved_criteria_weights = yager_data.get('criteria_weights', {})
    saved_expert_ratings = yager_data.get('expert_ratings', {})
    saved_num_experts = yager_data.get('num_experts', 3)
    
    return render_template('yager_input.html', 
                         project=project, 
                         criteria=criteria, 
                         alternatives=alternatives,
                         scale_options=scale_options,
                         saved_criteria_weights=saved_criteria_weights,
                         saved_expert_ratings=saved_expert_ratings,
                         saved_num_experts=saved_num_experts)


@app.route('/project/<int:project_id>/yager_results')
def yager_results(project_id):
    """Route untuk hasil perhitungan Yager KMKK"""
    project = Project.query.get_or_404(project_id)
    criteria = project.criteria
    alternatives = project.alternatives
    
    if len(criteria) == 0 or len(alternatives) == 0:
        return render_template('error.html', message='Kriteria dan alternatif harus ditambahkan terlebih dahulu')
    
    # Ambil data dari session
    yager_data = session.get('yager_data')
    if not yager_data:
        return redirect(url_for('yager_input', project_id=project_id))
    
    # Jalankan analisis Yager dengan data dinamis
    from methods import YagerMethod
    
    # Konversi data untuk YagerMethod
    criteria_weights = {}
    for crit in criteria:
        # Kunci session adalah string, jadi konversi crit.id ke string
        criteria_weights[crit.name] = yager_data['criteria_weights'].get(str(crit.id), 4)
    
    experts = {}
    for expert_name, expert_data in yager_data['expert_ratings'].items():
        experts[expert_name] = {}
        for alt in alternatives:
            experts[expert_name][alt.name] = {}
            for crit in criteria:
                # Kunci session adalah string, jadi konversi ID ke string
                rating = expert_data.get(str(alt.id), {}).get(str(crit.id), 4)
                experts[expert_name][alt.name][crit.name] = rating
    
    # Jalankan analisis
    results = YagerMethod.run_analysis_with_data(criteria_weights, experts)
    
    # Tambahkan data untuk template
    results['scale_map'] = YagerMethod.SCALE_MAP
    results['sorted_qualitative'] = {}
    for project_name, ratings in results['sorted_opinions'].items():
        results['sorted_qualitative'][project_name] = [YagerMethod.SCALE_MAP[r] for r in ratings]
    
    return render_template('yager_results.html', 
                         project=project, 
                         results=results,
                         criteria=criteria,
                         alternatives=alternatives)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
