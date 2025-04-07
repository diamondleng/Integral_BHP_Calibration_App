# Integral_BHP_Calibration_App
# Formation-Based Calibration Visualization App

This Streamlit web application visualizes bottom-hole pressure (BHP) calibration results using simulated and field data, filtered by geological formations.

## 🌐 Live App

[👉 Click here to open the app](https://your-streamlit-app-url.streamlit.app)  
*(Replace with actual URL after deploying)*

---

## 📂 What This App Does

1. **Upload three input files**:
   - **Calibration Result Excel**: Simulation BHP data
   - **Field Data Excel**: Measured field BHP (from B3 WHP)
   - **CMG Simulation `.dat` File**: Provides formation mapping for each well

2. **Select formations of interest** from a dropdown menu

3. **Visualize results**:
   - Scatter plot of simulated vs. measured BHP
   - 2D histogram showing data density
   - RMSE and confidence interval coverage

---

## 📄 Required Input Files

| File                         | Format     | Description                                             |
|------------------------------|------------|---------------------------------------------------------|
| `calibration_result.xlsx`    | `.xlsx`    | Must include columns: `Name`, `Date`, `Value`          |
| `field_data.xlsx`            | `.xlsx`    | Must include columns: `API_10`, `Injection Date`, `BHP_MDF_T` |
| `model.dat`                  | `.dat`     | CMG-formatted file with well/perforation section       |

---

## 🚀 How to Use the App

1. Go to the deployed app URL.
2. Upload the three required files.
3. Select one or more **formations** from the dropdown.
4. View the analysis: plots, statistics, and residuals.
5. Hover over points or colorbars to interpret results.

---

## 📦 Dependencies

Installed automatically on [Streamlit Cloud](https://streamlit.io/cloud) using `requirements.txt`:


---

## 👩‍💻 Local Development (Optional)

To run the app locally:

```bash
git clone https://github.com/your-username/formation-calibration-app.git
cd formation-calibration-app
pip install -r requirements.txt
streamlit run App_Test.py


📧 Contact
Developed by: Tim Jianqiao Leng
Affiliation: Center for Injectivity and Seismicity Research (CISR), UT Austin
Email: jianqiao.leng@beg.utexas.edu

