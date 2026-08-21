import Mathlib

/-!
# Quadratic extrema — Lean 4 + Mathlib 真证明
f(x) = a·x + b·x² 在 x* = -a/(2b) 处是局部极值。
-/

/-- f'(x) = a + 2·b·x — 一阶导数公式（FOC 的符号基础） -/
theorem quadratic_first_deriv {a b : ℝ} :
    deriv (fun x : ℝ => a * x + b * x ^ 2) = fun x => a + 2 * b * x := by
  funext x
  have hid : DifferentiableAt ℝ (fun x : ℝ => x) x := by fun_prop
  have hsq : DifferentiableAt ℝ (fun x : ℝ => x ^ 2) x := by fun_prop
  have hx : DifferentiableAt ℝ (fun x : ℝ => a * x) x := by fun_prop
  have hb2 : DifferentiableAt ℝ (fun x : ℝ => b * x ^ 2) x := by fun_prop
  change deriv ((fun x : ℝ => a * x) + fun x : ℝ => b * x ^ 2) x = a + 2 * b * x
  rw [deriv_add hx hb2]
  rw [deriv_const_mul a hid]
  rw [deriv_const_mul b hsq]
  change a * deriv (fun x : ℝ => x) x + b * deriv ((fun x : ℝ => x) ^ 2) x = a + 2 * b * x
  rw [deriv_pow hid 2]
  simp [deriv_id'']
  ring_nf

/-- b > 0 时，x* = -a/(2b) 是 f 的（全局，因而局部）最小值。 -/
theorem quadratic_minimum_unique {a b : ℝ} (hbpos : 0 < b) :
    IsLocalMin (fun x => a * x + b * x ^ 2) (-a / (2 * b)) := by
  rw [IsLocalMin, IsMinFilter]
  apply Filter.Eventually.of_forall
  intro x
  have hb : b ≠ 0 := ne_of_gt hbpos
  have hsq : a * x + b * x ^ 2 - (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2)
      = b * (x + a / (2 * b)) ^ 2 := by
    field_simp [hb]
    ring
  have hdiff : 0 ≤ a * x + b * x ^ 2 - (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2) := by
    rw [hsq]
    exact mul_nonneg (le_of_lt hbpos) (sq_nonneg (x + a / (2 * b)))
  linarith

/-- b < 0 时，x* = -a/(2b) 是 f 的（全局，因而局部）最大值。 -/
theorem quadratic_maximum_unique {a b : ℝ} (hbneg : b < 0) :
    IsLocalMax (fun x => a * x + b * x ^ 2) (-a / (2 * b)) := by
  rw [IsLocalMax, IsMaxFilter]
  apply Filter.Eventually.of_forall
  intro x
  have hb : b ≠ 0 := ne_of_lt hbneg
  have hsq : a * x + b * x ^ 2 - (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2)
      = b * (x + a / (2 * b)) ^ 2 := by
    field_simp [hb]
    ring
  have hdiff : a * x + b * x ^ 2 - (a * (-a / (2 * b)) + b * (-a / (2 * b)) ^ 2) ≤ 0 := by
    rw [hsq]
    exact mul_nonpos_of_nonpos_of_nonneg (le_of_lt hbneg) (sq_nonneg (x + a / (2 * b)))
  linarith
