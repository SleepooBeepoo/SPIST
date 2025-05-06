# Student CSV Import Feature

## Overview
This feature allows teachers to import multiple students into their subjects at once using a CSV file. The system will automatically create student accounts for new students and enroll them in the specified subject.

## How to Use

1. **Access the Import Feature**:
   - Log in as a teacher
   - Go to your dashboard
   - Find the subject you want to import students for
   - Click the "Import Students" button for that subject

2. **Prepare Your CSV File**:
   - Your CSV file must contain the following columns:
     - `Full Name`: The student's full name
     - `Course and Year`: The student's course and year (e.g., BSCS 1)
     - `Student Email`: The student's email address (must end with @spist.edu)
     - `Subject Code`: The code of the subject to enroll in (must match your subject code)

3. **Download the Template**:
   - On the import page, click the "Download CSV Template" button
   - This will download a sample CSV file that you can fill with your student data

4. **Upload Your CSV**:
   - Once your CSV file is ready, click the "Choose File" button
   - Select your CSV file
   - Click "Import Students"

5. **Review Results**:
   - The system will display a summary of the import process
   - It will show how many students were successfully imported, how many were already enrolled, how many new accounts were created, and any errors

## Sample CSV File

A sample CSV file has been created for testing purposes. You can find it at:

```
c:\Users\shizu\Desktop\Thesis\sample_student_import.csv
```

This file contains 5 sample student records that you can use to test the import feature.

## Notes

- New student accounts will be created with the default password: `changeme`
- Students should be instructed to change their password after first login
- Only students with emails ending in @spist.edu will be imported
- Only students with the matching subject code will be imported
- The system will automatically skip students who are already enrolled in the subject