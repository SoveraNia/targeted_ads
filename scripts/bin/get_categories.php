<?php
/**
 * Makes a request to AWIS for site info.
 */
class Categories {

    protected static $ActionName        = 'CategoryBrowse';
    protected static $ResponseGroupName = 'Categories';
    protected static $ServiceHost       = 'awis.amazonaws.com';
    protected static $SigVersion        = '2';
    protected static $HashAlgorithm     = 'HmacSHA256';
    protected static $Recursive         = 'True';

    public function Categories($accessKeyId, $secretAccessKey, $path) {
        $this->accessKeyId = $accessKeyId;
        $this->secretAccessKey = $secretAccessKey;
        $this->path = $path;
    }

    /**
     * Get site info from AWIS.
     */ 
    public function getCategories() {
        $queryParams = $this->buildQueryParams();
        $sig = $this->generateSignature($queryParams);
        $url = 'http://' . self::$ServiceHost . '/?' . $queryParams . 
            '&Signature=' . $sig;
        $ret = self::makeRequest($url);
        // echo "\nResults for " . $this->site .":\n\n";
        self::parseResponse($ret);
    }

    /**
     * Builds current ISO8601 timestamp.
     */
    protected static function getTimestamp() {
        return gmdate("Y-m-d\TH:i:s.\\0\\0\\0\\Z", time()); 
    }

    /**
     * Builds query parameters for the request to AWIS.
     * Parameter names will be in alphabetical order and
     * parameter values will be urlencoded per RFC 3986.
     * @return String query parameters for the request
     */
    protected function buildQueryParams() {
        $params = array(
            'Action'            => self::$ActionName,
            'ResponseGroup'     => self::$ResponseGroupName,
            'AWSAccessKeyId'    => $this->accessKeyId,
            'Timestamp'         => self::getTimestamp(),
            'SignatureVersion'  => self::$SigVersion,
            'SignatureMethod'   => self::$HashAlgorithm,
            'Path'              => $this->path
        );
        ksort($params);
        $keyvalue = array();
        foreach($params as $k => $v) {
            $keyvalue[] = $k . '=' . rawurlencode($v);
        }
        return implode('&',$keyvalue);
    }

    /**
     * Makes request to AWIS
     * @param String $url   URL to make request to
     * @return String       Result of request
     */
    protected static function makeRequest($url) {
        // echo "\nMaking request to:\n$url\n";
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_TIMEOUT, 4);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $result = curl_exec($ch);
        curl_close($ch);
        return $result;
    }

    /**
     * Parses XML response from AWIS and displays selected data
     * @param String $response    xml response from AWIS
     */
    public static function parseResponse($response) {
        $xml = new SimpleXMLElement($response,null,false,'http://awis.amazonaws.com/doc/2005-07-11');
        print_r(json_encode($xml));
        /*
        if($xml->count() && $xml->Response->UrlInfoResult->Alexa->count()) {
            $categories = $xml->Response->UrlInfoResult->Alexa->Related->Categories;
            // print_r(json_encode($categories));
        }
        */
    }

    /**
     * Generates an HMAC signature per RFC 2104.
     *
     * @param String $url       URL to use in createing signature
     */
    protected function generateSignature($url) {
        $sign = "GET\n" . strtolower(self::$ServiceHost) . "\n/\n". $url;
        // echo "String to sign: \n" . $sign . "\n";
        $sig = base64_encode(hash_hmac('sha256', $sign, $this->secretAccessKey, true));
        // echo "\nSignature: " . $sig ."\n";
        return rawurlencode($sig);
    }

}

$accessKeyId = 'AKIAJE4Z7LOVBPZWDP5A';//htmlspecialchars($_GET["accessKeyId"]);
$secretAccessKey = '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';//htmlspecialchars($_GET["secretAccessKey"]);

$path = $argv[1];

/*
$path = htmlspecialchars($_GET["path"]);
$start = htmlspecialchars($_GET["start"]);
$count = htmlspecialchars($_GET["count"]);
*/

$categories = new Categories($accessKeyId, $secretAccessKey, $path);
$categories->getCategories();

?>
