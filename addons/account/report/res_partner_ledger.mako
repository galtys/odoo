<html>
<head>
    <style type="text/css">
        ${css}
			.list_sale_table {
			border:thin solid #E3E4EA;
			text-align:center;
			border-collapse: collapse;
			}
			.list_sale_table td {
			border-top : thin solid #EEEEEE;
			text-align:right;
			font-size:12;
			padding-right:3px
			padding-left:3px
			padding-top:3px
			padding-bottom:3px
			}

			.list_bank_table {
			text-align:center;
			border-collapse: collapse;
			}
			.list_bank_table td {
			text-align:left;
			font-size:12;
			padding-right:3px
			padding-left:3px
			padding-top:3px
			padding-bottom:3px
			}

			.list_bank_table th {
			background-color: #EEEEEE;
			text-align:left;
			font-size:12;
			font-weight:bold;
			padding-right:3px
			padding-left:3px
			}
			
			.list_sale_table th {
			background-color: #EEEEEE;
			border: thin solid #000000;
			text-align:center;
			font-size:12;
			font-weight:bold;
			padding-right:3px
			padding-left:3px
			}
			
			.list_table thead {
			    display:table-header-group;
			}


			.list_tax_table {
			}
			.list_tax_table td {
			text-align:left;
			font-size:12;
			}
			
			.list_tax_table th {
			}


			.list_table thead {
			    display:table-header-group;
			}


			.list_total_table {
				border-collapse: collapse;
			}
			.list_total_table td {
			text-align:right;
			font-size:12;
			}

			.no_bloc {
				border-top: thin solid  #ffffff ;
			}

			
			.list_total_table th {
				background-color: #F7F7F7;
				border-collapse: collapse;
			}

            tfoot.totals tr:first-child td{
                padding-top: 15px;
            }



			.right_table {
			right: 4cm;
			width:"100%";
			}
			
			.std_text {
				font-size:12;
				}


    </style>
</head>
<body>
    <%page expression_filter="entity"/>
    <%
    def carriage_returns(text):
        return text.replace('\n', '<br />')

    %>
    %for p in objects:

    <h1 style="clear:both;">Partner Ledger</h1>

    <table class="basic_table" width="100%">
        <tr>
            <td style="font-weight:bold;">${_("Customer Ref")}</td>
            <td style="font-weight:bold;">${_("Customer Name")}</td>
            <td style="font-weight:bold;"></td>
        </tr>
        <tr>
            <td>${p.ref}</td>
	    <td>${p.name}</td>
            <td></td>
        </tr>
    </table>
    

    <table class="basic_table" width="100%">
        <tr>
            <td style="font-weight:bold;">Date</td>
            <td style="font-weight:bold;">JRNL</td>
            <td style="font-weight:bold;">move_name</td>
            <td style="font-weight:bold;">Account</td>
            <td style="font-weight:bold;">Ref</td>
            <td style="font-weight:bold;">Name</td>
	    <td style="font-weight:bold;">Reconcile</td>
	    
            <td style="font-weight:bold;">Debit</td>
	    <td style="font-weight:bold;">Credit</td>
	    <td style="font-weight:bold;">Balance</td>

        </tr>
    %for line in sorted(lines(p),key=lambda a:a['date'], reverse=True):
        <tr>
            <td>${line['date']}</td>
	    <td>${line['code']}</td>
            <td>${line['move_name']}</td>
            <td>${line['a_code']}</td>
            <td>${line['ref']}</td>
            <td>${line['name']}</td>
	    <td>${line['reconcile']}</td>
            <td>${line['debit']}</td>
            <td>${line['credit']}</td>
	    <td>${line['progress']}</td>

        </tr>
    %endfor
    </table>

<!--
    <div class="force_page_break"></div>
-->
    %endfor
</body>
</html>
