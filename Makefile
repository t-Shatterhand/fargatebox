.PHONY: clean

clean:
	@echo "Cleaning up .py and .zip files in ./lambda_code/"
	-@del /s /q lambda_code\*.py 2>nul || true
	-@del /s /q lambda_code\*.zip 2>nul || true