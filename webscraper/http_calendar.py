"""Main module of web requests"""
import re
from datetime import date, timedelta
from time import sleep

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry


def http_request(url, external_data):
    """Login, navigate, and download CSV from website."""

    yesterday = date.today() - timedelta(days = 1)

    with requests.Session() as web_session:
        retries = Retry(total=3,
                backoff_factor=0.2,
                status_forcelist=[ 500, 502, 503, 504 ])
        web_session.mount('https://', HTTPAdapter(max_retries=retries))

        # Gets required fields for login request for ASP.NET
        response = web_session.get(f'{url}/OperatorPortal/Login.aspx')
        soup = BeautifulSoup(response.content, 'html.parser')

        # Login to website
        response = web_session.post(
            f'{url}/OperatorPortal/Login.aspx',
            data={
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "__EVENTTARGE",
                "ctl00$radPaneLogo": external_data["ScreenSize"]["ctl00$radPaneLogo"],
                "ctl00$loginViewSignIn$imageButtonLogin.x": "61",
                "ctl00$loginViewSignIn$imageButtonLogin.y": "9",
                "ctl00$radPaneUserStatus": external_data["ScreenSize"]["ctl00$radPaneUserStatus"],
                "ctl00$TopPane": external_data["ScreenSize"]["ctl00$TopPane"],
                "ctl00$BodyPane": external_data["ScreenSize"]["ctl00$BodyPane"],
                "ctl00$radPaneFooter": external_data["ScreenSize"]["ctl00$TopPane"],
                "__VIEWSTATE": soup.select_one("#__VIEWSTATE")["value"],
                "__VIEWSTATEGENERATOR": soup.select_one("#__VIEWSTATEGENERATOR")["value"],
                "__EVENTVALIDATION": soup.select_one("#__EVENTVALIDATION")["value"],
                "ctl00$loginViewSignIn$textBoxUserId": external_data["TEXTBOXUSERID"],
                "ctl00$loginViewSignIn$textBoxPassword": external_data["TEXTBOXPASSWORD"]
            }
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        asp_net_session_id = f'ASP.NET_SessionId={str(web_session.cookies["ASP.NET_SessionId"])}; .ASPXFORMSAUTH={str(web_session.cookies[".ASPXFORMSAUTH"])}'


        web_session.headers.update(
            {
                "Host": url[8:],
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Origin": url,
                "DNT": "1",
                "Connection": "keep-alive",
                "Cookie": asp_net_session_id,
                "Sec-Fetch-Site": "same-origin",
            }
        )
        response = web_session.post(
            f'{url}/OperatorPortal/Reports.aspx',
            headers={
                "Accept": "*/*",
                "Referer": f'{url}/OperatorPortal/Reports.aspx',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
            },
            data={
                "__EVENTTARGET": "ctl00:contentPlaceHolderFeaturePanel:radAjaxManager",
                "__EVENTARGUMENT": "10",
                "__VIEWSTATE": soup.select_one("#__VIEWSTATE")["value"],
                "ctl00$radPaneLogo": external_data["ScreenSize"]["ctl00$radPaneLogo"],
                "ctl00$radPaneUserStatus": external_data["ScreenSize"]["ctl00$radPaneUserStatus"],
                "ctl00$TopPane": external_data["ScreenSize"]["ctl00$TopPane"],
                "ctl00$radPaneFeatureToolbar": external_data["ScreenSize"]["ctl00$radPaneFeatureToolbar"],
                "ctl00$contentPlaceHolderFeaturePanel$radTreeViewReports_expanded": "0100000",
                "ctl00$contentPlaceHolderFeaturePanel$radTreeViewReports_checked": "0000000",
                "ctl00$contentPlaceHolderFeaturePanel$radTreeViewReports_selected": "000000001",
                "ctl00$contentPlaceHolderFeaturePanel$radTreeViewReports_scroll": "0",
                "ctl00$contentPlaceHolderFeaturePanel$radTreeViewReports_viewstate": "0",
                "ctl00$radPaneLeftPaneFeaturePanel": external_data["ScreenSize"]["ctl00$radPaneLeftPaneFeaturePanel"],
                "ctl00$radpaneLeft": external_data["ScreenSize"]["ctl00$radpaneLeft"],
                "ctl00$contentPlaceHolderBody$radMultiPageReports_Selected": "0",
                "ctl00$radPaneBodyMainContent": external_data["ScreenSize"]["ctl00$radPaneBodyMainContent"],
                "ctl00$BodyPane": external_data["ScreenSize"]["ctl00$BodyPane"],
                "ctl00$radPaneFooter": external_data["ScreenSize"]["ctl00$TopPane"],
                "__VIEWSTATEGENERATOR": soup.select_one("#__VIEWSTATEGENERATOR")["value"],
                "__EVENTVALIDATION": soup.select_one("#__EVENTVALIDATION")["value"],
                "RadAJAXControlID": "contentPlaceHolderFeaturePanel_radAjaxManager",
                "httprequest": "true",
            },
        ) # Receive redirect to /OnDemandReports.aspx


        web_session.headers.update(
            {"Origin": None, "Upgrade-Insecure-Requests": "1", "Sec-Fetch-User": "?1"}
        )
        response = web_session.get(
            f'{url}/OperatorPortal/OnDemandReports.aspx',
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Referer": f'{url}/OperatorPortal/Reports.aspx',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
            },
        ) # Receive first view of webpage and ControlID
        soup = BeautifulSoup(response.content, 'html.parser')
        control_id = re.search(r'ControlID=([a-f\d]+)', response.content.decode('utf-8'))


        ################## Check status of server resources? ControlID required
        web_session.headers.update(
            {"Origin": url, "X-Requested-With": "XMLHttpRequest"}
        )
        response = web_session.post(
            f'{url}/OperatorPortal/Reserved.ReportViewerWebControl.axd',
            params={
                "OpType": "SessionKeepAlive",
                "ControlID": control_id,
            },
            headers={"Accept": "*/*", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors"},
        ) # Responce "OK"


        DatePickerStartDate = soup.select_one("#contentPlaceHolderFeaturePanel_radDatePickerStartDate")["value"]
        DatePickerStartDate_dateInput = soup.select_one(str("#contentPlaceHolderFeaturePanel_radDatePickerStartDate_dateInput"))["value"]
        DatePickerStartDate_dateInput_TextBox = soup.select_one(str("#contentPlaceHolderFeaturePanel_radDatePickerStartDate_dateInput_TextBox"))["value"]
        DatePickerStartDate_calendar_AD = soup.select_one(str("#contentPlaceHolderFeaturePanel_radDatePickerStartDate_calendar_AD"))["value"]
        DatePickerEndDate = soup.select_one("#contentPlaceHolderFeaturePanel_radDatePickerEndDate")["value"]
        DatePickerEndDate_dateInput = soup.select_one("#contentPlaceHolderFeaturePanel_radDatePickerEndDate_dateInput")["value"]
        DatePickerEndDate_dateInput_TextBox = soup.select_one(str("#contentPlaceHolderFeaturePanel_radDatePickerEndDate_dateInput_TextBox"))["value"]
        DatePickerEndDate_calendar_AD = soup.select_one(str("#contentPlaceHolderFeaturePanel_radDatePickerEndDate_calendar_AD"))["value"]
        ################## Request for current date
        web_session.headers.update({"X-MicrosoftAjax": "Delta=true", "Cache-Control": "no-cache"})
        response = web_session.post(
            f'{url}/OperatorPortal/OnDemandReports.aspx',
            headers={"Accept": "*/*", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors"},
            data={
                "ctl00$ScriptManager1": "ctl00$ScriptManager1|ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$Reserved_AsyncLoadTarget",
                "__EVENTTARGET": "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$Reserved_AsyncLoadTarget",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": soup.select_one("#__VIEWSTATE")["value"],
                "__VIEWSTATEGENERATOR": soup.select_one("#__VIEWSTATEGENERATOR")["value"],
                "__EVENTVALIDATION": soup.select_one("#__EVENTVALIDATION")["value"],
                "ctl00$radPaneLogo": "",
                "ctl00$radPaneUserStatus": "",
                "ctl00$TopPane": "",
                "ctl00$radPaneFeatureToolbar": "",
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate": DatePickerStartDate,
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerStartDate$dateInput": DatePickerStartDate_dateInput,
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerStartDate$dateInput_TextBox": DatePickerStartDate_dateInput_TextBox,
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate_calendar_SD": "[]",
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate_calendar_AD": DatePickerStartDate_calendar_AD,
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate": DatePickerEndDate,
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerEndDate$dateInput": DatePickerEndDate_dateInput,
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerEndDate$dateInput_TextBox": DatePickerEndDate_dateInput_TextBox,
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate_calendar_SD": "[]",
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate_calendar_AD": DatePickerEndDate_calendar_AD,
                "ctl00$radPaneLeftPaneFeaturePanel": "",
                "ctl00$radpaneLeft": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl03$ctl00": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl03$ctl01": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl11": "ltr",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl12": "standards",
                "ctl00$contentPlaceHolderBody$ReportViewer1$AsyncWait$HiddenCancelField": "False",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ToggleParam$store": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ToggleParam$collapse": "false",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl06$ctl00$CurrentPage": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl06$ctl03$ctl00": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl09$ClientClickedId": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl08$store": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl08$collapse": "false",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$VisibilityState$ctl00": "None",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ScrollPosition": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl02": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl03": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl04": "PageWidth",
                "ctl00$radPaneBodyMainContent": "",
                "ctl00$BodyPane": "",
                "ctl00$radPaneFooter": "",
                "__ASYNCPOST": "true",
                "": "",
            },
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        view_state = re.search(r'\|__VIEWSTATE\|(.*?)\|', response.content.decode('utf-8'))[1]
        view_state_generator = re.search(r'\|__VIEWSTATEGENERATOR\|(.*?)\|', response.content.decode('utf-8'))[1]
        event_validation = re.search(r'\|__EVENTVALIDATION\|(.*?)\|', response.content.decode('utf-8'))[1]
        sleep(2)


        ################## Change date picker
        web_session.headers.update({"Origin": url})
        response = web_session.post(
            f'{url}/OperatorPortal/OnDemandReports.aspx',
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
            },
            data={
                "ctl00$radPaneLogo": external_data["ScreenSize"]["ctl00$radPaneLogo"],
                "ctl00$radPaneUserStatus": external_data["ScreenSize"]["ctl00$radPaneUserStatus"],
                "ctl00$TopPane": external_data["ScreenSize"]["ctl00$TopPane"],
                "ctl00$radPaneFeatureToolbar": external_data["ScreenSize"]["ctl00$radPaneFeatureToolbar"],
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate": str(yesterday),
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerStartDate$dateInput": f'{str(yesterday)} 0:0:0',
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerStartDate$dateInput_TextBox": str(yesterday.strftime("%A , %B   %d, %Y")),
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate_calendar_SD": "[]",
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate_calendar_AD": DatePickerStartDate_calendar_AD,
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate": str(yesterday),
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerEndDate$dateInput": f'{str(yesterday)} 0:0:0',
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerEndDate$dateInput_TextBox": str(yesterday.strftime("%A , %B   %d, %Y")),
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate_calendar_SD": f'[[{str(yesterday.strftime("%Y,%m,%d"))}]]',
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate_calendar_AD": DatePickerEndDate_calendar_AD,
                "ctl00$contentPlaceHolderFeaturePanel$imageButtonApplyReportParameters.x": "32",
                "ctl00$contentPlaceHolderFeaturePanel$imageButtonApplyReportParameters.y": "7",
                "ctl00$radPaneLeftPaneFeaturePanel": external_data["ScreenSize"]["ctl00$radPaneLeftPaneFeaturePanel"],
                "ctl00$radpaneLeft": external_data["ScreenSize"]["ctl00$radpaneLeft"],
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl03$ctl00": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl03$ctl01": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl11": "ltr",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl12": "standards",
                "ctl00$contentPlaceHolderBody$ReportViewer1$AsyncWait$HiddenCancelField": "False",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ToggleParam$store": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ToggleParam$collapse": "false",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl06$ctl00$CurrentPage": "1",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl06$ctl03$ctl00": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl09$ClientClickedId": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl08$store": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl08$collapse": "false",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$VisibilityState$ctl00": "ReportPage",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ScrollPosition": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl02": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl03": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl04": "PageWidth",
                "ctl00$radPaneBodyMainContent": external_data["ScreenSize"]["ctl00$radPaneBodyMainContent"],
                "ctl00$BodyPane": external_data["ScreenSize"]["ctl00$BodyPane"],
                "ctl00$radPaneFooter": external_data["ScreenSize"]["ctl00$TopPane"],
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": view_state,
                "__VIEWSTATEGENERATOR": view_state_generator,
                "__EVENTVALIDATION": event_validation,
            },
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        view_state = re.search(r'\|__VIEWSTATE\|(.*?)\|', response.content.decode('utf-8'))[1]
        view_state_generator = re.search(r'\|__VIEWSTATEGENERATOR\|(.*?)\|', response.content.decode('utf-8'))[1]
        event_validation = re.search(r'\|__EVENTVALIDATION\|(.*?)\|', response.content.decode('utf-8'))[1]
        control_id = re.search(r'ControlID=([a-f\d]+)', response.content.decode('utf-8'))


        ################## Check status of server resources? ControlID required
        web_session.headers.update(
            {
                "Origin": url,
                "DNT": "1",
                "Connection": "keep-alive",
                "Cookie": asp_net_session_id,
                "Sec-Fetch-Site": "same-origin",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        response = web_session.post(
            f'{url}/OperatorPortal/Reserved.ReportViewerWebControl.axd',
            params={
                "OpType": "SessionKeepAlive",
                "ControlID": control_id,
            },
            headers={"Accept": "*/*", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors"},
        ) # Responce "OK"


        response = web_session.post(
            f'{url}/OperatorPortal/OnDemandReports.aspx',
            headers={
                "Accept": "*/*",
                "X-MicrosoftAjax": "Delta=true",
                "Cache-Control": "no-cache",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
            },
            data={
                "ctl00$ScriptManager1": "ctl00$ScriptManager1|ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$Reserved_AsyncLoadTarget",
                "__EVENTTARGET": "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$Reserved_AsyncLoadTarget",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": view_state,
                "__VIEWSTATEGENERATOR": view_state_generator,
                "__EVENTVALIDATION": event_validation,
                "ctl00$radPaneLogo": external_data["ScreenSize"]["ctl00$radPaneLogo"],
                "ctl00$radPaneUserStatus": external_data["ScreenSize"]["ctl00$radPaneUserStatus"],
                "ctl00$TopPane": external_data["ScreenSize"]["ctl00$TopPane"],
                "ctl00$radPaneFeatureToolbar": external_data["ScreenSize"]["ctl00$radPaneFeatureToolbar"],
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate": str(yesterday),
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerStartDate$dateInput": f'{str(yesterday)} 0:0:0',
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerStartDate$dateInput_TextBox": str(yesterday.strftime("%A , %B   %d, %Y")),
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate_calendar_SD": "[]",
                "contentPlaceHolderFeaturePanel_radDatePickerStartDate_calendar_AD": DatePickerStartDate_calendar_AD,
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate": str(yesterday),
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerEndDate$dateInput": f'{str(yesterday)} 0:0:0',
                "ctl00$contentPlaceHolderFeaturePanel$radDatePickerEndDate$dateInput_TextBox": str(yesterday.strftime("%A , %B   %d, %Y")),
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate_calendar_SD": "[[2023,1,21]]",
                "contentPlaceHolderFeaturePanel_radDatePickerEndDate_calendar_AD": DatePickerEndDate_calendar_AD,
                "ctl00$radPaneLeftPaneFeaturePanel": external_data["ScreenSize"]["ctl00$radPaneLeftPaneFeaturePanel"],
                "ctl00$radpaneLeft": external_data["ScreenSize"]["ctl00$radpaneLeft"],
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl03$ctl00": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl03$ctl01": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl11": "ltr",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl12": "standards",
                "ctl00$contentPlaceHolderBody$ReportViewer1$AsyncWait$HiddenCancelField": "False",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ToggleParam$store": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ToggleParam$collapse": "false",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl06$ctl00$CurrentPage": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl06$ctl03$ctl00": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl09$ClientClickedId": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl08$store": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl08$collapse": "false",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$VisibilityState$ctl00": "None",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ScrollPosition": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl02": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl03": "",
                "ctl00$contentPlaceHolderBody$ReportViewer1$ctl10$ReportControl$ctl04": "PageWidth",
                "ctl00$radPaneBodyMainContent": external_data["ScreenSize"]["ctl00$radPaneBodyMainContent"],
                "ctl00$BodyPane": external_data["ScreenSize"]["ctl00$BodyPane"],
                "ctl00$radPaneFooter": external_data["ScreenSize"]["ctl00$TopPane"],
                "__ASYNCPOST": "true",
                "": "",
            },
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        view_state = re.search(r'\|__VIEWSTATE\|(.*?)\|', response.content.decode('utf-8'))[1]
        view_state_generator = re.search(r'\|__VIEWSTATEGENERATOR\|(.*?)\|', response.content.decode('utf-8'))[1]
        event_validation = re.search(r'\|__EVENTVALIDATION\|(.*?)\|', response.content.decode('utf-8'))[1]
        control_id = re.search(r'ControlID=([a-f\d]+)', response.content.decode('utf-8'))[1]
        report_session = re.search(r'ReportSession=([a-z\d]+)', response.content.decode('utf-8'))[1]
        ui_culture = re.search(r'UICulture=(\d+)', response.content.decode('utf-8'))[1]


        # Download CSV files
        csv_output = web_session.get(
            f'{url}/OperatorPortal/Reserved.ReportViewerWebControl.axd',
            params={
                "ReportSession": report_session,
                "Culture": ui_culture,
                "CultureOverrides": "True",
                "UICulture": ui_culture,
                "UICultureOverrides": "True",
                "ReportStack": "1",
                "ControlID": control_id,
                "OpType": "Export",
                "FileName": "OpVLTRevenueBalAgainstCash",
                "ContentDisposition": "OnlyHtmlInline",
                "Format": "CSV",
            },
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
                "Cookie": asp_net_session_id,
                "Host": url[8:],
                "Referer": f'{url}/OperatorPortal/OnDemandReports.aspx',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
            },
        )

        return csv_output.content
