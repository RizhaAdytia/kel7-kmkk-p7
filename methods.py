"""
Modul untuk metode-metode pengambilan keputusan tambahan:
- MPE (Metode Perbandingan Eksponensial)
- Teorema Bayes (Pendekatan Nilai Harapan)
- CPI (Composite Performance Index)
"""

import numpy as np
from scipy import stats


class MPE:
    """Metode Perbandingan Eksponensial"""
    
    @staticmethod
    def calculate_scores(criteria_weights, alternative_values):
        """
        Menghitung skor menggunakan metode perbandingan eksponensial
        
        Args:
            criteria_weights: array bobot kriteria
            alternative_values: matrix nilai alternatif (n_alternatives x n_criteria)
        
        Returns:
            array skor alternatif
        """
        try:
            # Normalisasi nilai alternatif ke range (1, 9)
            alt_normalized = MPE._normalize_values(alternative_values)
            
            # Handle empty or invalid weights
            if len(criteria_weights) == 0 or np.sum(criteria_weights) == 0:
                criteria_weights = np.ones(len(criteria_weights)) / len(criteria_weights)
            
            # Normalize weights to sum to 1
            weights_normalized = criteria_weights / np.sum(np.abs(criteria_weights) + 1e-10)
            
            # Hitung skor dengan exponential weighting
            scores = []
            for alt_row in alt_normalized:
                try:
                    # Gunakan exponential weighted sum dengan error handling
                    exp_weights = np.exp(weights_normalized)
                    score = np.sum(alt_row * exp_weights)
                    scores.append(max(score, 0.0))
                except:
                    scores.append(0.0)
            
            # Normalisasi skor akhir
            scores = np.array(scores)
            score_sum = np.sum(scores)
            if score_sum > 0:
                scores = scores / score_sum
            else:
                scores = np.ones(len(scores)) / len(scores)
            
            return scores
        except Exception as e:
            # Fallback: return uniform scores if calculation fails
            return np.ones(len(alternative_values)) / len(alternative_values)
    
    @staticmethod
    def calculate_scores_advanced(criteria_weights, alternative_values):
        """
        Versi advanced dengan power exponential
        """
        try:
            alt_normalized = MPE._normalize_values(alternative_values)
            
            # Handle empty or invalid weights
            if len(criteria_weights) == 0 or np.sum(np.abs(criteria_weights)) == 0:
                criteria_weights = np.ones(len(criteria_weights)) / len(criteria_weights)
            
            # Normalize weights
            weights_normalized = np.abs(criteria_weights) / (np.sum(np.abs(criteria_weights)) + 1e-10)
            
            scores = []
            for alt_row in alt_normalized:
                try:
                    # Ensure positive values for power operation
                    safe_row = np.maximum(alt_row, 0.1)
                    weighted_values = safe_row ** np.maximum(weights_normalized, 0.1)
                    score = np.prod(weighted_values)
                    scores.append(max(score, 0.0))
                except:
                    scores.append(0.0)
            
            scores = np.array(scores)
            score_sum = np.sum(scores)
            if score_sum > 0:
                scores = scores / score_sum
            else:
                scores = np.ones(len(scores)) / len(scores)
            
            return scores
        except Exception as e:
            # Fallback: return uniform scores
            return np.ones(len(alternative_values)) / len(alternative_values)
    
    @staticmethod
    def _normalize_values(values):
        """Normalisasi nilai ke range (1, 9)"""
        try:
            if values.size == 0:
                return values
            
            min_val = np.min(values)
            max_val = np.max(values)
            
            if max_val - min_val == 0 or np.isnan(max_val - min_val):
                return np.full_like(values, 5.0, dtype=float)
            
            normalized = 1 + (values - min_val) * 8 / (max_val - min_val)
            normalized = np.clip(normalized, 1, 9)
            normalized = np.where(np.isnan(normalized), 5.0, normalized)
            
            return normalized
        except Exception as e:
            return np.full_like(values, 5.0, dtype=float)


class BayesMethod:
    """Teorema Bayes dengan Pendekatan Nilai Harapan"""
    
    @staticmethod
    def calculate_expected_values(criteria_weights, alternative_values, 
                                   prior_probabilities=None):
        """
        Menghitung nilai harapan menggunakan Teorema Bayes
        
        Args:
            criteria_weights: array bobot kriteria (prior probabilities)
            alternative_values: matrix nilai alternatif
            prior_probabilities: prior probabilities untuk setiap alternatif (optional)
        
        Returns:
            dict dengan posterior probabilities dan expected values
        """
        try:
            n_alt = alternative_values.shape[0]
            
            # Initialize prior probabilities jika tidak diberikan
            if prior_probabilities is None:
                prior_probabilities = np.ones(n_alt) / n_alt
            
            # Ensure valid arrays
            prior_probabilities = np.asarray(prior_probabilities, dtype=float)
            criteria_weights = np.asarray(criteria_weights, dtype=float)
            
            # Hitung likelihood untuk setiap alternatif pada setiap kriteria
            likelihoods = BayesMethod._calculate_likelihoods(alternative_values)
            
            # Hitung posterior probability dengan Bayes' theorem
            posterior_probs = BayesMethod._calculate_posterior(
                prior_probabilities,
                likelihoods,
                criteria_weights
            )
            
            # Hitung expected values
            expected_values = BayesMethod._calculate_expected_value(
                posterior_probs,
                alternative_values
            )
            
            return {
                'prior': prior_probabilities,
                'posterior': posterior_probs,
                'expected_values': expected_values,
                'likelihoods': likelihoods
            }
        except Exception as e:
            # Fallback: return uniform distributions
            n_alt = alternative_values.shape[0] if len(alternative_values.shape) > 0 else 1
            uniform = np.ones(n_alt) / max(n_alt, 1)
            return {
                'prior': uniform,
                'posterior': uniform,
                'expected_values': uniform,
                'likelihoods': np.full((n_alt, alternative_values.shape[1] if len(alternative_values.shape) > 1 else 1), 0.5)
            }
    
    @staticmethod
    def _calculate_likelihoods(alternative_values):
        """
        Hitung likelihood scores menggunakan normalisasi
        """
        try:
            # Normalisasi setiap kolom (kriteria) ke (0, 1)
            likelihoods = []
            for col_idx in range(alternative_values.shape[1]):
                col = alternative_values[:, col_idx]
                min_val = np.min(col)
                max_val = np.max(col)
                
                if max_val - min_val == 0 or np.isnan(max_val - min_val):
                    normalized_col = np.full_like(col, 0.5, dtype=float)
                else:
                    normalized_col = (col - min_val) / (max_val - min_val)
                    normalized_col = np.clip(normalized_col, 0, 1)
                    normalized_col = np.where(np.isnan(normalized_col), 0.5, normalized_col)
                
                likelihoods.append(normalized_col)
            
            return np.array(likelihoods).T  # (n_alt, n_criteria)
        except Exception as e:
            # Fallback: return 0.5 for all
            return np.full((alternative_values.shape[0], alternative_values.shape[1]), 0.5)
    
    @staticmethod
    def calculate_posterior(prior, likelihoods, criteria_weights):
        """
        Menghitung posterior probability menggunakan Bayes' theorem
        P(A|B) = P(B|A) * P(A) / P(B)
        """
        try:
            # Handle edge cases
            if len(prior) == 0 or len(likelihoods) == 0 or len(criteria_weights) == 0:
                return np.ones(len(prior)) / len(prior) if len(prior) > 0 else np.array([])
            
            # Normalize criteria weights
            weights_sum = np.sum(np.abs(criteria_weights))
            if weights_sum == 0:
                weights_norm = np.ones(len(criteria_weights)) / len(criteria_weights)
            else:
                weights_norm = np.abs(criteria_weights) / weights_sum
            
            # P(B|A) untuk setiap alternatif
            likelihood_given_alt = np.sum(np.clip(likelihoods, 0, 1) * weights_norm, axis=1)
            
            # P(B) = average likelihood
            p_b = np.mean(likelihood_given_alt)
            
            if p_b == 0 or np.isnan(p_b):
                p_b = 1.0 / len(prior)
            
            # P(A|B) = P(B|A) * P(A) / P(B)
            posterior = (likelihood_given_alt * np.clip(prior, 0, 1)) / (p_b + 1e-10)
            
            # Normalisasi dan handle NaN
            posterior = np.clip(posterior, 0, 1)
            posterior_sum = np.sum(posterior)
            
            if posterior_sum > 0:
                posterior = posterior / posterior_sum
            else:
                posterior = np.ones(len(prior)) / len(prior)
            
            # Replace any NaN with uniform
            posterior = np.where(np.isnan(posterior), 1.0/len(prior), posterior)
            
            return posterior
        except Exception as e:
            return np.ones(len(prior)) / len(prior) if len(prior) > 0 else np.array([])
    
    @staticmethod
    def _calculate_expected_value(posterior_probs, alternative_values):
        """
        Hitung expected value E(X) = Σ(x * P(x))
        """
        try:
            posterior_probs = np.asarray(posterior_probs, dtype=float)
            
            # Normalisasi alternative_values untuk expected value calculation
            normalized_alts = np.mean(alternative_values, axis=1)
            
            if len(normalized_alts) == 0:
                return np.array([])
            
            min_val = np.min(normalized_alts)
            max_val = np.max(normalized_alts)
            
            if max_val - min_val == 0 or np.isnan(max_val - min_val):
                normalized_alts = np.full_like(normalized_alts, 0.5, dtype=float)
            else:
                normalized_alts = (normalized_alts - min_val) / (max_val - min_val)
                normalized_alts = np.clip(normalized_alts, 0, 1)
            
            # Handle NaN
            normalized_alts = np.where(np.isnan(normalized_alts), 0.5, normalized_alts)
            
            expected_values = normalized_alts * posterior_probs
            expected_values = np.where(np.isnan(expected_values), 0, expected_values)
            
            return expected_values
        except Exception as e:
            return np.ones(len(alternative_values))


class CPI:
    """Composite Performance Index"""
    
    @staticmethod
    def calculate_cpi_weighted_sum(criteria_weights, alternative_values):
        """
        Menghitung CPI menggunakan weighted sum method
        CPI(i) = Σ(w(j) * x(i,j))
        
        Args:
            criteria_weights: array bobot kriteria
            alternative_values: matrix nilai alternatif
        
        Returns:
            array CPI scores
        """
        try:
            # Normalisasi nilai alternatif ke range (0, 1)
            normalized_alts = CPI._normalize_to_01(alternative_values)
            
            # Normalize weights
            weights_sum = np.sum(np.abs(criteria_weights))
            if weights_sum == 0 or np.isnan(weights_sum):
                weights_norm = np.ones(len(criteria_weights)) / len(criteria_weights)
            else:
                weights_norm = np.abs(criteria_weights) / weights_sum
            
            # Hitung CPI sebagai weighted sum
            cpi_scores = normalized_alts @ weights_norm
            
            # Ensure output is valid
            cpi_scores = np.clip(cpi_scores, 0, 1)
            cpi_scores = np.where(np.isnan(cpi_scores), 0.5, cpi_scores)
            
            return cpi_scores
        except Exception as e:
            # Fallback: return uniform scores
            return np.ones(len(alternative_values)) / len(alternative_values)
    
    @staticmethod
    def calculate_cpi_geometric_mean(criteria_weights, alternative_values):
        """
        Menghitung CPI menggunakan geometric mean method dengan weights
        CPI(i) = (∏(x(i,j)^w(j)))^(1/Σw(j))
        
        Ini memberikan prioritas pada keseimbangan performa
        """
        try:
            normalized_alts = CPI._normalize_to_01(alternative_values)
            
            # Normalize weights
            weights_sum = np.sum(np.abs(criteria_weights))
            if weights_sum == 0 or np.isnan(weights_sum):
                weights_norm = np.ones(len(criteria_weights)) / len(criteria_weights)
            else:
                weights_norm = np.abs(criteria_weights) / weights_sum
            
            cpi_scores = []
            for alt_row in normalized_alts:
                try:
                    # Geometric mean dengan weights
                    safe_row = np.maximum(alt_row, 0.01)  # Avoid log(0)
                    log_values = np.log(safe_row)
                    weighted_log = np.sum(weights_norm * log_values)
                    weighted_product = np.exp(weighted_log)
                    normalized_score = np.power(weighted_product, 1.0 / (np.sum(weights_norm) + 1e-10))
                    cpi_scores.append(np.clip(normalized_score, 0, 1))
                except:
                    cpi_scores.append(0.5)
            
            scores = np.array(cpi_scores)
            scores = np.where(np.isnan(scores), 0.5, scores)
            return scores
        except Exception as e:
            return np.ones(len(alternative_values)) / len(alternative_values)
    
    @staticmethod
    def calculate_cpi_root_mean_square(criteria_weights, alternative_values):
        """
        Menghitung CPI menggunakan root mean square method
        CPI(i) = √(Σ(w(j) * x(i,j)²))
        
        Ini lebih sensitif terhadap nilai yang tinggi
        """
        try:
            normalized_alts = CPI._normalize_to_01(alternative_values)
            
            # Normalize weights
            weights_sum = np.sum(np.abs(criteria_weights))
            if weights_sum == 0 or np.isnan(weights_sum):
                weights_norm = np.ones(len(criteria_weights)) / len(criteria_weights)
            else:
                weights_norm = np.abs(criteria_weights) / weights_sum
            
            cpi_scores = []
            for alt_row in normalized_alts:
                try:
                    squared_weighted = weights_norm * (alt_row ** 2)
                    cpi_score = np.sqrt(np.sum(squared_weighted))
                    cpi_scores.append(np.clip(cpi_score, 0, 1))
                except:
                    cpi_scores.append(0.5)
            
            scores = np.array(cpi_scores)
            scores = np.where(np.isnan(scores), 0.5, scores)
            return scores
        except Exception as e:
            return np.ones(len(alternative_values)) / len(alternative_values)
    
    @staticmethod
    def calculate_full_cpi_report(criteria_weights, alternative_values):
        """
        Menghitung semua metode CPI dan membandingkannya
        """
        try:
            weighted_sum = CPI.calculate_cpi_weighted_sum(criteria_weights, alternative_values)
            geometric_mean = CPI.calculate_cpi_geometric_mean(criteria_weights, alternative_values)
            rms = CPI.calculate_cpi_root_mean_square(criteria_weights, alternative_values)
            
            # Hitung average CPI
            average_cpi = (weighted_sum + geometric_mean + rms) / 3
            average_cpi = np.clip(average_cpi, 0, 1)
            average_cpi = np.where(np.isnan(average_cpi), 0.5, average_cpi)
            
            return {
                'weighted_sum': weighted_sum,
                'geometric_mean': geometric_mean,
                'root_mean_square': rms,
                'average': average_cpi
            }
        except Exception as e:
            # Fallback: return uniform scores
            uniform = np.ones(len(alternative_values)) / len(alternative_values)
            return {
                'weighted_sum': uniform,
                'geometric_mean': uniform,
                'root_mean_square': uniform,
                'average': uniform
            }
    
    @staticmethod
    def _normalize_to_01(values):
        """Normalisasi nilai ke range (0, 1)"""
        try:
            # Handle edge cases
            if values.size == 0:
                return values
            
            min_val = np.min(values, axis=0)
            max_val = np.max(values, axis=0)
            
            # Hindari division by zero
            range_val = max_val - min_val
            range_val = np.where(range_val == 0, 1, range_val)
            
            normalized = (values - min_val) / range_val
            
            # Clip to ensure values are in [0, 1]
            normalized = np.clip(normalized, 0, 1)
            
            # Replace NaN with 0.5
            normalized = np.where(np.isnan(normalized), 0.5, normalized)
            
            return normalized
        except Exception as e:
            return np.full_like(values, 0.5, dtype=float)
    
    @staticmethod
    def calculate_consistency_measure(cpi_scores):
        """
        Menghitung consistency measure untuk CPI scores
        Menggunakan coefficient of variation
        """
        try:
            cpi_scores = np.asarray(cpi_scores, dtype=float)
            
            # Handle edge cases
            if len(cpi_scores) == 0:
                return {
                    'mean': 0,
                    'std_dev': 0,
                    'coefficient_variation': 0,
                    'ranking_stability': 1.0
                }
            
            # Remove NaN values
            valid_scores = cpi_scores[~np.isnan(cpi_scores)]
            
            if len(valid_scores) == 0:
                return {
                    'mean': 0,
                    'std_dev': 0,
                    'coefficient_variation': 0,
                    'ranking_stability': 1.0
                }
            
            mean_score = np.mean(valid_scores)
            
            if mean_score == 0:
                return {
                    'mean': mean_score,
                    'std_dev': 0,
                    'coefficient_variation': 0,
                    'ranking_stability': 1.0
                }
            
            std_dev = np.std(valid_scores)
            cv = std_dev / abs(mean_score)  # Coefficient of Variation
            
            return {
                'mean': float(mean_score),
                'std_dev': float(std_dev),
                'coefficient_variation': float(cv),
                'ranking_stability': float(1 - min(cv, 1))  # Cap at 1
            }
        except Exception as e:
            return {
                'mean': 0,
                'std_dev': 0,
                'coefficient_variation': 0,
                'ranking_stability': 1.0
            }


# Helper functions
def normalize_matrix(matrix):
    """Normalisasi matrix ke range (0, 1)"""
    min_val = np.min(matrix)
    max_val = np.max(matrix)
    
    if max_val - min_val == 0:
        return np.full_like(matrix, 0.5, dtype=float)
    
    return (matrix - min_val) / (max_val - min_val)


def extract_alternative_values_from_comparisons(project, criteria, Comparison):
    """
    Extract nilai alternatif dari comparison data
    Mengkonversi perbandingan pairwise menjadi estimated values
    
    Args:
        project: Project object
        criteria: list of Criterion objects
        Comparison: Comparison model class dari app
    
    Returns:
        matrix (n_alternatives x n_criteria)
    """
    alternatives = project.alternatives
    n_alt = len(alternatives)
    n_crit = len(criteria)
    
    alt_values = np.ones((n_alt, n_crit)) * 5.0  # Default middle value
    
    for crit_idx, criterion in enumerate(criteria):
        # Ambil rating untuk setiap alternatif pada kriteria ini
        for alt_idx, alternative in enumerate(alternatives):
            # Cari nilai perbandingan
            rating = 5.0  # Default middle value
            
            try:
                comparisons = Comparison.query.filter_by(
                    criterion_id=criterion.id,
                    type='alternatives'
                ).all()
                
                # Hitung estimated value dari comparative judgments
                ratings_for_alt = []
                for comp in comparisons:
                    try:
                        if comp.item1_id == alt_idx:
                            if comp.value > 0:
                                ratings_for_alt.append(comp.value)
                        elif comp.item2_id == alt_idx:
                            if comp.value > 0:
                                ratings_for_alt.append(1.0 / comp.value)
                    except:
                        continue
                
                if ratings_for_alt and len(ratings_for_alt) > 0:
                    try:
                        # Hitung geometric mean dengan error handling
                        log_values = [np.log(max(val, 0.1)) for val in ratings_for_alt if val > 0]
                        if log_values:
                            rating = np.exp(np.mean(log_values))
                    except:
                        rating = np.mean(ratings_for_alt) if ratings_for_alt else 5.0
            except:
                rating = 5.0
            
            alt_values[alt_idx, crit_idx] = max(0.1, min(rating, 9.0))  # Clamp to (0.1, 9.0)
    
    return alt_values


# ==================== METODE SAW (Simple Additive Weighting) ====================

class SAW:
    """
    Simple Additive Weighting (SAW) Method
    
    Metode SAW adalah teknik penjumlahan terbobot dengan normalisasi matriks keputusan.
    Proses meliputi:
    1. Normalisasi matriks keputusan (X) menjadi matriks (R)
    2. Perkalian matriks ternormalisasi dengan bobot kriteria
    3. Penjumlahan hasil perkalian untuk setiap alternatif
    """
    
    def __init__(self, decision_matrix, is_benefit):
        """
        Args:
            decision_matrix: matrix (n_alternatives x n_criteria)
            is_benefit: array boolean indicating benefit (True) atau cost (False) criteria
        """
        self.decision_matrix = np.asarray(decision_matrix, dtype=float)
        self.is_benefit = np.asarray(is_benefit, dtype=bool)
        self.n_alt, self.n_crit = self.decision_matrix.shape
    
    def calculate(self, weights):
        """
        Hitung SAW scores
        
        Args:
            weights: array bobot kriteria (harus sum to 1 atau akan dinormalisasi)
        
        Returns:
            dict dengan normalized_matrix, weighted_matrix, final_scores, rankings
        """
        try:
            weights = np.asarray(weights, dtype=float)
            
            # Normalize weights to sum to 1
            weight_sum = np.sum(weights)
            if weight_sum <= 0:
                weights = np.ones(len(weights)) / len(weights)
            else:
                weights = weights / weight_sum
            
            # Step 1: Normalize decision matrix (R)
            normalized_matrix = self._normalize_matrix()
            
            # Step 2: Calculate weighted matrix (V = R * w)
            weighted_matrix = normalized_matrix * weights
            
            # Step 3: Calculate final scores (Sum of weighted matrix per alternative)
            final_scores = np.sum(weighted_matrix, axis=1)
            
            # Step 4: Calculate rankings
            rankings = self._get_rankings(final_scores)
            
            return {
                'normalized_matrix': normalized_matrix,
                'weighted_matrix': weighted_matrix,
                'final_scores': final_scores,
                'rankings': rankings,
                'weights': weights
            }
        except Exception as e:
            return self._fallback_result()
    
    def _normalize_matrix(self):
        """
        Normalisasi matriks keputusan
        
        Untuk kriteria Benefit (Max): R_ij = X_ij / Max(X_j)
        Untuk kriteria Cost (Min): R_ij = Min(X_j) / X_ij
        """
        normalized = np.zeros_like(self.decision_matrix, dtype=float)
        
        for j in range(self.n_crit):
            column = self.decision_matrix[:, j]
            
            if self.is_benefit[j]:
                # Benefit: divide by max
                max_val = np.max(column)
                if max_val > 0:
                    normalized[:, j] = column / max_val
                else:
                    normalized[:, j] = 0.5
            else:
                # Cost: divide min by value
                min_val = np.min(column)
                safe_col = np.maximum(column, 1e-10)
                if min_val > 0:
                    normalized[:, j] = min_val / safe_col
                else:
                    normalized[:, j] = 0.5
        
        # Ensure values are in valid range
        normalized = np.clip(normalized, 0, 1)
        normalized = np.where(np.isnan(normalized), 0.5, normalized)
        
        return normalized
    
    def _get_rankings(self, scores):
        """Konversi scores ke rankings (1 = best)"""
        sorted_indices = np.argsort(scores)[::-1]  # Descending
        rankings = np.empty_like(sorted_indices)
        rankings[sorted_indices] = np.arange(1, len(scores) + 1)
        return rankings
    
    def _fallback_result(self):
        """Return uniform scores jika ada error"""
        uniform_scores = np.ones(self.n_alt) / self.n_alt
        rankings = np.arange(1, self.n_alt + 1)
        return {
            'normalized_matrix': np.ones((self.n_alt, self.n_crit)) * 0.5,
            'weighted_matrix': np.ones((self.n_alt, self.n_crit)) * 0.5,
            'final_scores': uniform_scores,
            'rankings': rankings,
            'weights': np.ones(self.n_crit) / self.n_crit
        }


# ==================== METODE PROMETHEE II ====================

class PROMETHEE:
    """
    PROMETHEE II (Preference Ranking Organization METHod for Enrichment Evaluations)
    
    Metode outranking yang menggunakan preference functions untuk membandingkan alternatif.
    Proses meliputi:
    1. Hitung selisih nilai untuk setiap pasangan alternatif per kriteria
    2. Terapkan preference function (P)
    3. Hitung indeks preferensi agregat π(a,b)
    4. Hitung leaving flow (φ+) dan entering flow (φ-)
    5. Hitung net flow (φ = φ+ - φ-) untuk ranking final
    """
    
    def __init__(self, decision_matrix, is_benefit):
        """
        Args:
            decision_matrix: matrix (n_alternatives x n_criteria)
            is_benefit: array boolean indicating benefit (True) atau cost (False) criteria
        """
        self.decision_matrix = np.asarray(decision_matrix, dtype=float)
        self.is_benefit = np.asarray(is_benefit, dtype=bool)
        self.n_alt, self.n_crit = self.decision_matrix.shape
    
    def calculate(self, weights, params):
        """
        Hitung PROMETHEE II scores
        
        Args:
            weights: array bobot kriteria
            params: list of tuples (p, q) untuk setiap kriteria
        
        Returns:
            dict dengan phi_plus, phi_minus, phi_net, rankings, dan detail matriks
        """
        try:
            weights = np.asarray(weights, dtype=float)
            
            # Normalize weights
            weight_sum = np.sum(weights)
            if weight_sum <= 0:
                weights = np.ones(len(weights)) / len(weights)
            else:
                weights = weights / weight_sum
            
            # Step 1: Calculate pairwise differences
            differences = self._calculate_differences()
            
            # Step 2: Calculate preference degrees (P) using linear preference function
            preference_degrees = self._calculate_preference_degrees(differences, params)
            
            # Step 3: Calculate aggregate preference index π(a,b)
            aggregate_index = self._calculate_preference_index(preference_degrees, weights)
            
            # Step 4: Calculate flows
            phi_plus = self._calculate_leaving_flow(aggregate_index)
            phi_minus = self._calculate_entering_flow(aggregate_index)
            phi_net = phi_plus - phi_minus
            
            # Step 5: Calculate rankings
            rankings = self._get_rankings(phi_net)
            
            return {
                'phi_plus': phi_plus,
                'phi_minus': phi_minus,
                'phi_net': phi_net,
                'rankings': rankings,
                'preference_degrees': preference_degrees,
                'aggregate_index': aggregate_index,
                'weights': weights
            }
        except Exception as e:
            return self._fallback_result()
    
    def _calculate_differences(self):
        """
        Hitung selisih nilai antara setiap pasangan alternatif
        d_jk(a,b) = f_j(a) - f_j(b) untuk semua j
        
        Returns:
            array (n_alt, n_alt, n_crit) dengan differences
        """
        differences = np.zeros((self.n_alt, self.n_alt, self.n_crit))
        
        for a in range(self.n_alt):
            for b in range(self.n_alt):
                for j in range(self.n_crit):
                    if self.is_benefit[j]:
                        # For benefit: d = a - b
                        differences[a, b, j] = self.decision_matrix[a, j] - self.decision_matrix[b, j]
                    else:
                        # For cost: d = b - a (invert)
                        differences[a, b, j] = self.decision_matrix[b, j] - self.decision_matrix[a, j]
        
        return differences
    
    def _calculate_preference_degrees(self, differences, params):
        """
        Terapkan linear preference function (Tipe V dalam PROMETHEE)
        
        P(d) = 0           if d <= q
             = (d-q)/(p-q) if q < d < p
             = 1           if d >= p
        
        Args:
            differences: array differences (n_alt, n_alt, n_crit)
            params: list of (p, q) tuples per kriteria
        
        Returns:
            array (n_alt, n_alt, n_crit) dengan preference degrees
        """
        preference_degrees = np.zeros_like(differences)
        
        for j in range(self.n_crit):
            p_j = params[j][0]  # preference threshold
            q_j = params[j][1]  # indifference threshold
            
            for a in range(self.n_alt):
                for b in range(self.n_alt):
                    d = differences[a, b, j]
                    
                    # Linear preference function
                    if d <= q_j:
                        preference_degrees[a, b, j] = 0
                    elif d >= p_j:
                        preference_degrees[a, b, j] = 1
                    else:
                        # Linear interpolation
                        preference_degrees[a, b, j] = (d - q_j) / (p_j - q_j)
        
        return preference_degrees
    
    def _calculate_preference_index(self, preference_degrees, weights):
        """
        Hitung indeks preferensi agregat π(a,b)
        π(a,b) = Σ(w_j * P_j(a,b))
        
        Args:
            preference_degrees: array (n_alt, n_alt, n_crit)
            weights: array bobot kriteria
        
        Returns:
            array (n_alt, n_alt) dengan aggregate preference index
        """
        aggregate_index = np.zeros((self.n_alt, self.n_alt))
        
        for a in range(self.n_alt):
            for b in range(self.n_alt):
                weighted_sum = 0
                for j in range(self.n_crit):
                    weighted_sum += weights[j] * preference_degrees[a, b, j]
                aggregate_index[a, b] = weighted_sum
        
        return aggregate_index
    
    def _calculate_leaving_flow(self, aggregate_index):
        """
        Hitung leaving flow (positive flow)
        φ+(a) = (1/(n-1)) * Σ π(a,b) untuk semua b ≠ a
        """
        phi_plus = np.zeros(self.n_alt)
        
        for a in range(self.n_alt):
            sum_preference = 0
            for b in range(self.n_alt):
                if a != b:
                    sum_preference += aggregate_index[a, b]
            phi_plus[a] = sum_preference / (self.n_alt - 1) if self.n_alt > 1 else 0
        
        return phi_plus
    
    def _calculate_entering_flow(self, aggregate_index):
        """
        Hitung entering flow (negative flow)
        φ-(a) = (1/(n-1)) * Σ π(b,a) untuk semua b ≠ a
        """
        phi_minus = np.zeros(self.n_alt)
        
        for a in range(self.n_alt):
            sum_preference = 0
            for b in range(self.n_alt):
                if a != b:
                    sum_preference += aggregate_index[b, a]
            phi_minus[a] = sum_preference / (self.n_alt - 1) if self.n_alt > 1 else 0
        
        return phi_minus
    
    def _get_rankings(self, phi_net):
        """Konversi net flow ke rankings (1 = best)"""
        sorted_indices = np.argsort(phi_net)[::-1]  # Descending
        rankings = np.empty_like(sorted_indices)
        rankings[sorted_indices] = np.arange(1, len(phi_net) + 1)
        return rankings
    
    def _fallback_result(self):
        """Return uniform results jika ada error"""
        uniform_flows = np.ones(self.n_alt) / self.n_alt
        rankings = np.arange(1, self.n_alt + 1)
        return {
            'phi_plus': uniform_flows,
            'phi_minus': uniform_flows,
            'phi_net': np.zeros(self.n_alt),
            'rankings': rankings,
            'preference_degrees': np.ones((self.n_alt, self.n_alt, self.n_crit)) * 0.5,
            'aggregate_index': np.ones((self.n_alt, self.n_alt)) * 0.5,
            'weights': np.ones(self.n_crit) / self.n_crit
        }


class YagerMethod:
    """
    Metodologi Ronald R. Yager untuk Pengambilan Keputusan Kelompok Multi Kriteria (KMKK) Kualitatif
    
    Implementasi algoritma Yager dengan skala kualitatif 1-7:
    7=S (Sempurna), 6=SB (Sangat Baik), 5=B (Baik), 4=Sd (Sedang),
    3=K (Kurang), 2=SK (Sangat Kurang), 1=BS (Buruk Sekali)
    
    Proses:
    1. Penilaian Individu tiap pakar menggunakan metode Minimax
    2. Agregasi pendapat pakar menggunakan metode OWA & Maximin
    """
    
    # Mapping skala kualitatif
    SCALE_MAP = {
        7: 'S', 6: 'SB', 5: 'B', 4: 'Sd', 
        3: 'K', 2: 'SK', 1: 'BS'
    }
    
    REVERSE_SCALE_MAP = {v: k for k, v in SCALE_MAP.items()}
    
    @staticmethod
    def neg(s):
        """
        Fungsi Negasi: Neg(S_i) = S_(q - i + 1), dengan q = 7
        
        Args:
            s: nilai skala (1-7)
        
        Returns:
            nilai negasi (1-7)
        """
        return 8 - s
    
    @staticmethod
    def max_val(a, b):
        """
        Fungsi Max: nilai terbesar antara dua nilai
        
        Args:
            a, b: nilai numerik
        
        Returns:
            nilai maksimum
        """
        return max(a, b)
    
    @staticmethod
    def min_val(a, b):
        """
        Fungsi Min: nilai terkecil antara dua nilai
        
        Args:
            a, b: nilai numerik
        
        Returns:
            nilai minimum
        """
        return min(a, b)
    
    @staticmethod
    def calculate_individual_evaluation(criteria_weights, expert_ratings):
        """
        Langkah 1: Penilaian Individu tiap pakar (Metode Minimax)
        
        P_ir = Min_j [ Max(Neg(I_j), P_ir^j) ]
        
        Args:
            criteria_weights: dict bobot kriteria {'C1': 6, 'C2': 5, 'C3': 4}
            expert_ratings: dict penilaian pakar untuk proyek tertentu
                          {'C1': 5, 'C2': 4, 'C3': 6}
        
        Returns:
            nilai evaluasi individu (1-7)
        """
        min_values = []
        
        for criterion, weight in criteria_weights.items():
            neg_weight = YagerMethod.neg(weight)
            rating = expert_ratings[criterion]
            max_val = YagerMethod.max_val(neg_weight, rating)
            min_values.append(max_val)
        
        return YagerMethod.min_val(min_values[0], YagerMethod.min_val(min_values[1], min_values[2]))
    
    @staticmethod
    def calculate_aggregation_thresholds(r=3, q=7):
        """
        Hitung nilai fungsi batas Q(k) untuk agregasi
        
        Q(k) = int[1 + (k * (q-1)/r)]
        
        Args:
            r: jumlah pakar (default 3)
            q: skala maksimum (default 7)
        
        Returns:
            list Q values [Q(1), Q(2), Q(3)]
        """
        q_values = []
        for k in range(1, r + 1):
            b_k = 1 + (k * (q - 1) / r)
            q_values.append(int(b_k))
        return q_values
    
    @staticmethod
    def calculate_group_aggregation(individual_ratings, q_values=[3, 5, 7]):
        """
        Langkah 2: Agregasi Pendapat Pakar (Metode OWA & Maximin)
        
        P_i = Max_k [ Min(Q(k), B_k) ]
        
        Args:
            individual_ratings: list nilai P_ir dari ketiga pakar [p1, p2, p3]
            q_values: list nilai Q [3, 5, 7]
        
        Returns:
            nilai agregasi akhir (1-7)
        """
        # Urutkan descending
        b_values = sorted(individual_ratings, reverse=True)
        
        # Hitung Max_k Min(Q(k), B_k)
        max_values = []
        for k in range(len(q_values)):
            min_val = YagerMethod.min_val(q_values[k], b_values[k])
            max_values.append(min_val)
        
        return max(max_values)
    
    @staticmethod
    def get_mock_data():
        """
        Mengembalikan data mock penilaian pakar
        
        Returns:
            dict dengan struktur:
            {
                'criteria_weights': {'C1': 6, 'C2': 5, 'C3': 4},
                'experts': {
                    'PK1': {'Proyek A': {'C1': 5, 'C2': 4, 'C3': 6}, ...},
                    ...
                }
            }
        """
        criteria_weights = {'C1': 6, 'C2': 5, 'C3': 4}  # SB, B, Sd
        
        experts = {
            'PK1': {
                'Proyek A': {'C1': 5, 'C2': 4, 'C3': 6},  # B, Sd, SB
                'Proyek B': {'C1': 6, 'C2': 5, 'C3': 4},  # SB, B, Sd
                'Proyek C': {'C1': 3, 'C2': 4, 'C3': 3}   # K, Sd, K
            },
            'PK2': {
                'Proyek A': {'C1': 6, 'C2': 5, 'C3': 7},  # SB, B, S
                'Proyek B': {'C1': 5, 'C2': 5, 'C3': 5},  # B, B, B
                'Proyek C': {'C1': 4, 'C2': 3, 'C3': 3}   # Sd, K, K
            },
            'PK3': {
                'Proyek A': {'C1': 7, 'C2': 6, 'C3': 6},  # S, SB, SB
                'Proyek B': {'C1': 6, 'C2': 6, 'C3': 5},  # SB, SB, B
                'Proyek C': {'C1': 5, 'C2': 4, 'C3': 2}   # B, Sd, SK
            }
        }
        
        return {
            'criteria_weights': criteria_weights,
            'experts': experts
        }
    
    @staticmethod
    def run_analysis_with_data(criteria_weights, experts):
        """
        Menjalankan analisis lengkap KMKK menggunakan metodologi Yager dengan data dinamis
        
        Args:
            criteria_weights: dict bobot kriteria {'nama_kriteria': nilai_skala}
            experts: dict penilaian pakar {
                'PK1': {
                    'nama_alternatif': {
                        'nama_kriteria': nilai_skala
                    }
                }
            }
        
        Returns:
            dict hasil analisis
        """
        # Proyek dan pakar
        projects = list(experts[list(experts.keys())[0]].keys())
        expert_names = list(experts.keys())
        
        # Hitung Q values
        r = len(expert_names)
        q_values = YagerMethod.calculate_aggregation_thresholds(r)
        
        # Hasil individu per pakar
        individual_results = {}
        for expert in expert_names:
            individual_results[expert] = {}
            for project in projects:
                p_ir = YagerMethod.calculate_individual_evaluation(
                    criteria_weights, 
                    experts[expert][project]
                )
                individual_results[expert][project] = p_ir
        
        # Agregasi kelompok
        group_results = {}
        sorted_opinions = {}
        
        for project in projects:
            # Ambil nilai dari ketiga pakar
            ratings = [individual_results[expert][project] for expert in expert_names]
            
            # Urutkan descending untuk display
            sorted_ratings = sorted(ratings, reverse=True)
            sorted_opinions[project] = sorted_ratings
            
            # Hitung agregasi akhir
            final_score = YagerMethod.calculate_group_aggregation(ratings, q_values)
            group_results[project] = final_score
        
        # Tentukan proyek terbaik
        best_project = max(group_results, key=group_results.get)
        
        # Siapkan output
        output = {
            'individual_evaluations': individual_results,
            'sorted_opinions': sorted_opinions,
            'group_results': group_results,
            'best_project': best_project,
            'q_values': q_values,
            'num_experts': r
        }
        
        return output
    
    @staticmethod
    def print_results():
        """
        Menampilkan hasil analisis pada console sesuai spesifikasi
        """
        results = YagerMethod.run_analysis()
        
        print("=== ANALISIS KMKK METODOLOGI RONALD R. YAGER ===\n")
        
        # 1. Hasil evaluasi individu tiap pakar
        print("1. HASIL EVALUASI INDIVIDU TIAP PAKAR:")
        for expert, projects in results['individual_evaluations'].items():
            print(f"\n{expert}:")
            for project, score in projects.items():
                qualitative = YagerMethod.SCALE_MAP[score]
                print(f"   {project}: {qualitative} ({score})")
        
        # 2. Urutan menurun (B_k) dari pendapat pakar
        print("\n2. URUTAN MENURUN PENDAPAT PAKAR TIAP PROYEK:")
        for project, sorted_ratings in results['sorted_opinions'].items():
            qualitative_ratings = [YagerMethod.SCALE_MAP[r] for r in sorted_ratings]
            print(f"{project}: {qualitative_ratings} -> {sorted_ratings}")
        
        # 3. Hasil akhir agregasi
        print("\n3. HASIL AKHIR AGREGASI KEPUTUSAN KELOMPOK:")
        print(f"Nilai Q: {results['q_values']}")
        for project, score in results['group_results'].items():
            qualitative = YagerMethod.SCALE_MAP[score]
            print(f"{project}: {qualitative} ({score})")
        
        # Proyek terbaik
        best = results['best_project']
        best_score = results['group_results'][best]
        best_qualitative = YagerMethod.SCALE_MAP[best_score]
        print(f"\nPROYEK PALING LAYAK DIPILIH: {best} dengan nilai {best_qualitative} ({best_score})")
