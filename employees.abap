*&---------------------------------------------------------------------*
*& Report Z_EMPLOYEE_MANAGEMENT
*& Employee Management System - Complete ABAP Program
*&---------------------------------------------------------------------*
REPORT z_employee_management.

*----------------------------------------------------------------------*
* Type Definitions
*----------------------------------------------------------------------*
TYPES: BEGIN OF ty_employee,
         emp_id      TYPE i,
         first_name  TYPE string,
         last_name   TYPE string,
         department  TYPE string,
         position    TYPE string,
         salary      TYPE p DECIMALS 2,
         hire_date   TYPE d,
         active      TYPE abap_bool,
       END OF ty_employee.

TYPES: BEGIN OF ty_department_stats,
         department  TYPE string,
         emp_count   TYPE i,
         avg_salary  TYPE p DECIMALS 2,
         total_salary TYPE p DECIMALS 2,
       END OF ty_department_stats.

*----------------------------------------------------------------------*
* Data Declarations
*----------------------------------------------------------------------*
DATA: lt_employees      TYPE TABLE OF ty_employee,
      ls_employee       TYPE ty_employee,
      lt_dept_stats     TYPE TABLE OF ty_department_stats,
      ls_dept_stat      TYPE ty_department_stats,
      lv_total_employees TYPE i,
      lv_active_count    TYPE i,
      lv_total_payroll   TYPE p DECIMALS 2.

*----------------------------------------------------------------------*
* Selection Screen
*----------------------------------------------------------------------*
SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
PARAMETERS: p_dept TYPE string DEFAULT 'ALL',
            p_minsal TYPE p DECIMALS 2 DEFAULT 0,
            p_active AS CHECKBOX DEFAULT 'X'.
SELECTION-SCREEN END OF BLOCK b1.

*----------------------------------------------------------------------*
* Class Definition - Employee Manager
*----------------------------------------------------------------------*
CLASS lcl_employee_manager DEFINITION.
  PUBLIC SECTION.
    METHODS: constructor,
             add_employee IMPORTING is_employee TYPE ty_employee,
             get_all_employees RETURNING VALUE(rt_employees) TYPE STANDARD TABLE,
             calculate_department_stats RETURNING VALUE(rt_stats) TYPE STANDARD TABLE,
             filter_by_department IMPORTING iv_dept TYPE string
                                  RETURNING VALUE(rt_employees) TYPE STANDARD TABLE,
             filter_by_salary IMPORTING iv_min_salary TYPE p
                              RETURNING VALUE(rt_employees) TYPE STANDARD TABLE,
             get_employee_count RETURNING VALUE(rv_count) TYPE i,
             calculate_total_payroll RETURNING VALUE(rv_total) TYPE p,
             promote_employee IMPORTING iv_emp_id TYPE i
                                        iv_new_position TYPE string
                                        iv_new_salary TYPE p,
             terminate_employee IMPORTING iv_emp_id TYPE i,
             display_employee_report,
             display_department_summary.

  PRIVATE SECTION.
    DATA: mt_employees TYPE TABLE OF ty_employee.

    METHODS: calculate_bonus IMPORTING iv_salary TYPE p
                             RETURNING VALUE(rv_bonus) TYPE p,
             format_name IMPORTING iv_first TYPE string
                                   iv_last TYPE string
                         RETURNING VALUE(rv_full_name) TYPE string.
ENDCLASS.

*----------------------------------------------------------------------*
* Class Implementation - Employee Manager
*----------------------------------------------------------------------*
CLASS lcl_employee_manager IMPLEMENTATION.

  METHOD constructor.
    " Initialize with sample data
    DATA: ls_emp TYPE ty_employee.

    ls_emp-emp_id = 1001.
    ls_emp-first_name = 'John'.
    ls_emp-last_name = 'Smith'.
    ls_emp-department = 'Engineering'.
    ls_emp-position = 'Senior Developer'.
    ls_emp-salary = '95000.00'.
    ls_emp-hire_date = '20200115'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1002.
    ls_emp-first_name = 'Sarah'.
    ls_emp-last_name = 'Johnson'.
    ls_emp-department = 'Engineering'.
    ls_emp-position = 'Tech Lead'.
    ls_emp-salary = '125000.00'.
    ls_emp-hire_date = '20190301'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1003.
    ls_emp-first_name = 'Michael'.
    ls_emp-last_name = 'Chen'.
    ls_emp-department = 'Finance'.
    ls_emp-position = 'Financial Analyst'.
    ls_emp-salary = '78000.00'.
    ls_emp-hire_date = '20210601'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1004.
    ls_emp-first_name = 'Emily'.
    ls_emp-last_name = 'Davis'.
    ls_emp-department = 'Finance'.
    ls_emp-position = 'Senior Accountant'.
    ls_emp-salary = '88000.00'.
    ls_emp-hire_date = '20200807'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1005.
    ls_emp-first_name = 'Robert'.
    ls_emp-last_name = 'Wilson'.
    ls_emp-department = 'Sales'.
    ls_emp-position = 'Sales Manager'.
    ls_emp-salary = '105000.00'.
    ls_emp-hire_date = '20180920'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1006.
    ls_emp-first_name = 'Jessica'.
    ls_emp-last_name = 'Martinez'.
    ls_emp-department = 'Sales'.
    ls_emp-position = 'Sales Representative'.
    ls_emp-salary = '65000.00'.
    ls_emp-hire_date = '20220315'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1007.
    ls_emp-first_name = 'David'.
    ls_emp-last_name = 'Brown'.
    ls_emp-department = 'Engineering'.
    ls_emp-position = 'Junior Developer'.
    ls_emp-salary = '72000.00'.
    ls_emp-hire_date = '20230110'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1008.
    ls_emp-first_name = 'Amanda'.
    ls_emp-last_name = 'Taylor'.
    ls_emp-department = 'HR'.
    ls_emp-position = 'HR Manager'.
    ls_emp-salary = '92000.00'.
    ls_emp-hire_date = '20190815'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1009.
    ls_emp-first_name = 'James'.
    ls_emp-last_name = 'Anderson'.
    ls_emp-department = 'Engineering'.
    ls_emp-position = 'Senior Developer'.
    ls_emp-salary = '98000.00'.
    ls_emp-hire_date = '20210401'.
    ls_emp-active = abap_false.
    APPEND ls_emp TO mt_employees.

    ls_emp-emp_id = 1010.
    ls_emp-first_name = 'Lisa'.
    ls_emp-last_name = 'Thompson'.
    ls_emp-department = 'Sales'.
    ls_emp-position = 'Sales Representative'.
    ls_emp-salary = '68000.00'.
    ls_emp-hire_date = '20220701'.
    ls_emp-active = abap_true.
    APPEND ls_emp TO mt_employees.
  ENDMETHOD.

  METHOD add_employee.
    APPEND is_employee TO mt_employees.
  ENDMETHOD.

  METHOD get_all_employees.
    rt_employees = mt_employees.
  ENDMETHOD.

  METHOD calculate_department_stats.
    DATA: lt_temp_employees TYPE TABLE OF ty_employee,
          ls_temp_employee  TYPE ty_employee,
          ls_stat           TYPE ty_department_stats,
          lt_departments    TYPE TABLE OF string,
          lv_dept           TYPE string,
          lv_count          TYPE i,
          lv_total          TYPE p DECIMALS 2.

    " Get unique departments
    LOOP AT mt_employees INTO ls_temp_employee WHERE active = abap_true.
      READ TABLE lt_departments WITH KEY table_line = ls_temp_employee-department TRANSPORTING NO FIELDS.
      IF sy-subrc <> 0.
        APPEND ls_temp_employee-department TO lt_departments.
      ENDIF.
    ENDLOOP.

    " Calculate stats for each department
    LOOP AT lt_departments INTO lv_dept.
      CLEAR: lv_count, lv_total, ls_stat.

      LOOP AT mt_employees INTO ls_temp_employee WHERE department = lv_dept AND active = abap_true.
        lv_count = lv_count + 1.
        lv_total = lv_total + ls_temp_employee-salary.
      ENDLOOP.

      ls_stat-department = lv_dept.
      ls_stat-emp_count = lv_count.
      ls_stat-total_salary = lv_total.
      IF lv_count > 0.
        ls_stat-avg_salary = lv_total / lv_count.
      ENDIF.

      APPEND ls_stat TO rt_stats.
    ENDLOOP.
  ENDMETHOD.

  METHOD filter_by_department.
    DATA: ls_emp TYPE ty_employee.

    LOOP AT mt_employees INTO ls_emp WHERE department = iv_dept.
      APPEND ls_emp TO rt_employees.
    ENDLOOP.
  ENDMETHOD.

  METHOD filter_by_salary.
    DATA: ls_emp TYPE ty_employee.

    LOOP AT mt_employees INTO ls_emp WHERE salary >= iv_min_salary.
      APPEND ls_emp TO rt_employees.
    ENDLOOP.
  ENDMETHOD.

  METHOD get_employee_count.
    DATA: ls_emp TYPE ty_employee.

    rv_count = 0.
    LOOP AT mt_employees INTO ls_emp WHERE active = abap_true.
      rv_count = rv_count + 1.
    ENDLOOP.
  ENDMETHOD.

  METHOD calculate_total_payroll.
    DATA: ls_emp TYPE ty_employee.

    rv_total = 0.
    LOOP AT mt_employees INTO ls_emp WHERE active = abap_true.
      rv_total = rv_total + ls_emp-salary.
    ENDLOOP.
  ENDMETHOD.

  METHOD promote_employee.
    DATA: ls_emp TYPE ty_employee.

    LOOP AT mt_employees INTO ls_emp WHERE emp_id = iv_emp_id.
      ls_emp-position = iv_new_position.
      ls_emp-salary = iv_new_salary.
      MODIFY mt_employees FROM ls_emp INDEX sy-tabix.
      EXIT.
    ENDLOOP.
  ENDMETHOD.

  METHOD terminate_employee.
    DATA: ls_emp TYPE ty_employee.

    LOOP AT mt_employees INTO ls_emp WHERE emp_id = iv_emp_id.
      ls_emp-active = abap_false.
      MODIFY mt_employees FROM ls_emp INDEX sy-tabix.
      EXIT.
    ENDLOOP.
  ENDMETHOD.

  METHOD calculate_bonus.
    " Calculate 10% bonus
    rv_bonus = iv_salary * '0.10'.
  ENDMETHOD.

  METHOD format_name.
    CONCATENATE iv_first iv_last INTO rv_full_name SEPARATED BY space.
  ENDMETHOD.

  METHOD display_employee_report.
    DATA: ls_emp TYPE ty_employee,
          lv_full_name TYPE string,
          lv_bonus TYPE p DECIMALS 2,
          lv_years_service TYPE i,
          lv_current_date TYPE d.

    lv_current_date = sy-datum.

    WRITE: / '========================================'.
    WRITE: / 'EMPLOYEE DETAILED REPORT'.
    WRITE: / '========================================'.
    SKIP.

    LOOP AT mt_employees INTO ls_emp.
      lv_full_name = format_name( iv_first = ls_emp-first_name iv_last = ls_emp-last_name ).
      lv_bonus = calculate_bonus( ls_emp-salary ).

      " Calculate years of service
      lv_years_service = ( lv_current_date - ls_emp-hire_date ) DIV 365.

      WRITE: / 'Employee ID:', ls_emp-emp_id.
      WRITE: / '  Name:', lv_full_name.
      WRITE: / '  Department:', ls_emp-department.
      WRITE: / '  Position:', ls_emp-position.
      WRITE: / '  Salary: $', ls_emp-salary.
      WRITE: / '  Annual Bonus: $', lv_bonus.
      WRITE: / '  Hire Date:', ls_emp-hire_date.
      WRITE: / '  Years of Service:', lv_years_service.
      WRITE: / '  Status:', COND #( WHEN ls_emp-active = abap_true THEN 'Active' ELSE 'Inactive' ).
      SKIP.
    ENDLOOP.
  ENDMETHOD.

  METHOD display_department_summary.
    DATA: lt_stats TYPE TABLE OF ty_department_stats,
          ls_stat TYPE ty_department_stats.

    lt_stats = calculate_department_stats( ).

    WRITE: / '========================================'.
    WRITE: / 'DEPARTMENT SUMMARY REPORT'.
    WRITE: / '========================================'.
    SKIP.

    LOOP AT lt_stats INTO ls_stat.
      WRITE: / 'Department:', ls_stat-department.
      WRITE: / '  Number of Employees:', ls_stat-emp_count.
      WRITE: / '  Total Payroll: $', ls_stat-total_salary.
      WRITE: / '  Average Salary: $', ls_stat-avg_salary.
      SKIP.
    ENDLOOP.
  ENDMETHOD.

ENDCLASS.

*----------------------------------------------------------------------*
* Main Program Logic
*----------------------------------------------------------------------*
START-OF-SELECTION.

  DATA: lo_manager TYPE REF TO lcl_employee_manager,
        lt_filtered_employees TYPE TABLE OF ty_employee,
        ls_filtered_employee TYPE ty_employee.

  " Create employee manager instance
  CREATE OBJECT lo_manager.

  " Display header
  WRITE: / '****************************************************'.
  WRITE: / '*     EMPLOYEE MANAGEMENT SYSTEM - MAIN REPORT     *'.
  WRITE: / '****************************************************'.
  SKIP 2.

  " Display filter criteria
  WRITE: / 'FILTER CRITERIA:'.
  WRITE: / '  Department:', p_dept.
  WRITE: / '  Minimum Salary: $', p_minsal.
  WRITE: / '  Active Only:', COND #( WHEN p_active = 'X' THEN 'Yes' ELSE 'No' ).
  SKIP 2.

  " Get all employees and apply filters
  lt_filtered_employees = lo_manager->get_all_employees( ).

  " Apply department filter
  IF p_dept <> 'ALL'.
    DELETE lt_filtered_employees WHERE department <> p_dept.
  ENDIF.

  " Apply salary filter
  DELETE lt_filtered_employees WHERE salary < p_minsal.

  " Apply active status filter
  IF p_active = 'X'.
    DELETE lt_filtered_employees WHERE active <> abap_true.
  ENDIF.

  " Display filtered employee list
  WRITE: / '========================================'.
  WRITE: / 'FILTERED EMPLOYEE LIST'.
  WRITE: / '========================================'.
  SKIP.

  IF lines( lt_filtered_employees ) > 0.
    WRITE: / 'ID', 10 'Name', 35 'Department', 55 'Position', 80 'Salary', 100 'Status'.
    WRITE: / sy-uline(130).

    LOOP AT lt_filtered_employees INTO ls_filtered_employee.
      DATA(lv_display_name) = |{ ls_filtered_employee-first_name } { ls_filtered_employee-last_name }|.
      DATA(lv_status) = COND string( WHEN ls_filtered_employee-active = abap_true THEN 'Active' ELSE 'Inactive' ).

      WRITE: / ls_filtered_employee-emp_id UNDER 'ID',
               lv_display_name UNDER 'Name',
               ls_filtered_employee-department UNDER 'Department',
               ls_filtered_employee-position UNDER 'Position',
               ls_filtered_employee-salary UNDER 'Salary',
               lv_status UNDER 'Status'.
    ENDLOOP.
  ELSE.
    WRITE: / 'No employees match the filter criteria.'.
  ENDIF.

  SKIP 3.

  " Display department summary
  lo_manager->display_department_summary( ).

  SKIP 2.

  " Display statistics
  lv_total_employees = lo_manager->get_employee_count( ).
  lv_total_payroll = lo_manager->calculate_total_payroll( ).

  WRITE: / '========================================'.
  WRITE: / 'COMPANY STATISTICS'.
  WRITE: / '========================================'.
  WRITE: / 'Total Active Employees:', lv_total_employees.
  WRITE: / 'Total Annual Payroll: $', lv_total_payroll.
  IF lv_total_employees > 0.
    DATA(lv_avg_company_salary) = lv_total_payroll / lv_total_employees.
    WRITE: / 'Average Employee Salary: $', lv_avg_company_salary.
  ENDIF.

  SKIP 2.

  " Demonstrate employee operations
  WRITE: / '========================================'.
  WRITE: / 'PERFORMING EMPLOYEE OPERATIONS'.
  WRITE: / '========================================'.
  SKIP.

  " Promote an employee
  WRITE: / 'Promoting Employee 1007 (David Brown)...'.
  lo_manager->promote_employee( iv_emp_id = 1007
                                 iv_new_position = 'Mid-Level Developer'
                                 iv_new_salary = '85000.00' ).
  WRITE: / '  New Position: Mid-Level Developer'.
  WRITE: / '  New Salary: $85,000.00'.
  SKIP.

  " Add a new employee
  WRITE: / 'Adding new employee...'.
  CLEAR ls_employee.
  ls_employee-emp_id = 1011.
  ls_employee-first_name = 'Rachel'.
  ls_employee-last_name = 'Garcia'.
  ls_employee-department = 'HR'.
  ls_employee-position = 'Recruiter'.
  ls_employee-salary = '62000.00'.
  ls_employee-hire_date = sy-datum.
  ls_employee-active = abap_true.
  lo_manager->add_employee( ls_employee ).
  WRITE: / '  Added: Rachel Garcia - HR Recruiter'.
  SKIP.

  " Update statistics
  lv_total_employees = lo_manager->get_employee_count( ).
  lv_total_payroll = lo_manager->calculate_total_payroll( ).

  WRITE: / '========================================'.
  WRITE: / 'UPDATED STATISTICS'.
  WRITE: / '========================================'.
  WRITE: / 'Total Active Employees:', lv_total_employees.
  WRITE: / 'Total Annual Payroll: $', lv_total_payroll.

  SKIP 2.
  WRITE: / '****************************************************'.
  WRITE: / '*              END OF REPORT                       *'.
  WRITE: / '****************************************************'.

END-OF-SELECTION.
