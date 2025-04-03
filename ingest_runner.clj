(ns ingest-runner
  (:require [mxh.bolus2.core :as bolus2]
            [mxh.bolus2.boloid :as boloid]
            [clojure.java.io :as io]))

(defn -main
  "CLI entry point for ingestion via bolus2.
   Usage:
     clojure -M:dev -i ingest_runner.clj --main ingest-runner <path-to-dicoms>

   Expects environment variables:
     BOLUS2_PARTNER_NAME
     BOLUS2_PASSWORD
   (You can set these in a .env file or in your shell environment.)"
  [& args]
  (if (empty? args)
    (do
      (println "Usage: ingest-runner <path-to-dicoms>")
      (System/exit 1))
    (let [dicoms-path   (first args)
          sentinel-file (io/file dicoms-path "ingestion_complete.txt")
          partner-name  (System/getenv "BOLUS2_PARTNER_NAME")
          password      (System/getenv "BOLUS2_PASSWORD")]
      
      (when (or (nil? partner-name) (nil? password))
        (println "[ERROR] Missing environment variable(s). Please set BOLUS2_PARTNER_NAME and BOLUS2_PASSWORD.")
        (System/exit 1))
      
      (println "[INFO] Attempting to ingest from" dicoms-path)
      (when-not (.isDirectory (io/file dicoms-path))
        (println "[ERROR] The path does not exist or is not a directory:" dicoms-path)
        (System/exit 1))

      (try
        (bolus2/send-boloids!
          (boloid/gen-sequence {:source :fs :base-path dicoms-path})
          {:partner-name partner-name
           :password     password})
        (println "[INFO] Ingestion completed successfully!")
        ;; sentinel file to signal completion
        (spit sentinel-file "ingestion complete")
        (System/exit 0)

        (catch Exception e
          (println "[ERROR] bolus2 ingestion failed =>" (.getMessage e))
          (System/exit 1))))))

;; Allows running this file directly with bb/clj:
(when (= *file* (System/getProperty "babashka.file"))
  (-main *command-line-args*))
