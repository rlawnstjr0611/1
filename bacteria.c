#include<stdio.h>

int now_bacteria(int bacteria, int immune_bacteria){
	if(bacteria < 0){
		bacteria -= bacteria; //일반 박테리아 수를 음수가 아닌 정수로 맞추기 
	}
	printf("현재 일반 세균 수 : %d\n", bacteria); //일반 박테리아 수 출력 
	printf("현재 면역 세균 수 : %d\n", immune_bacteria); //면역 박테리아 수 출력 
	printf("총합 : %d\n", bacteria + immune_bacteria); //총합 출력 
	
	return bacteria; //음수가 아닌 정수로 맞추어진 일반 박테리아 수를 반환 
}

int main(){
	unsigned int bacteria, immune_bacteria, kill, i, j; //i, j는 for문에서 사용함 
	unsigned int kill_cnt = 1; //항생제 투여 횟수 
	unsigned int increase_cnt = 1; //증식 횟수 
	
	
	printf("일반 세균의 수를 입력하세요.\n");
	scanf("%d", &bacteria);
	printf("항생제 면역 세균의 수를 입력하세요.\n");
	scanf("%d", &immune_bacteria);
	printf("항생제로 죽일 세균의 수를 입력하세요.\n");
	scanf("%d", &kill);
	
	
	while(bacteria > 0)
	{
		switch(bacteria + immune_bacteria >= 50)  
		{
			case true: //세균 총 합이 50마리 이상일 시 항생제 투여
				printf("항생제 %d 회 투여 시작\n", kill_cnt);
				bacteria -= kill; 
				
				bacteria = now_bacteria(bacteria, immune_bacteria);
				
				kill_cnt ++;
				break;
			default: //그 외 상황에선 증식 
				printf("세균 %d 회 증식 시작\n", increase_cnt);
				bacteria *= 2;
				immune_bacteria *= 2;
				
				bacteria = now_bacteria(bacteria, immune_bacteria);
				
				increase_cnt ++;
				break;
		}
	}
	
	return 0;
} 
